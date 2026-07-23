import numpy as np
import logging
import json
from sqlalchemy import text
from typing import List, Dict, Any, Tuple
from app.config.settings import settings
from app.db.models import Document
from app.db.session import is_sqlite

logger = logging.getLogger(__name__)

# Initialize LLM embedding client dynamically
def get_embeddings_client():
    if settings.GOOGLE_API_KEY:
        try:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            model_name = settings.EMBEDDING_MODEL
            if "text-embedding" in model_name and "gemini" not in model_name:
                model_name = "models/gemini-embedding-001"
            return GoogleGenerativeAIEmbeddings(
                model=model_name,
                google_api_key=settings.GOOGLE_API_KEY
            )
        except Exception as e:
            logger.warning(f"Failed to load Google Embeddings: {e}")
            
    if settings.OPENAI_API_KEY:
        try:
            from langchain_openai import OpenAIEmbeddings
            return OpenAIEmbeddings(
                model=settings.EMBEDDING_MODEL or "text-embedding-3-small",
                # pyrefly: ignore [unexpected-keyword]
                openai_api_key=settings.OPENAI_API_KEY
            )
        except Exception as e:
            logger.warning(f"Failed to load OpenAI Embeddings: {e}")
            
    raise ValueError("No valid Embeddings API key configured. Please set GOOGLE_API_KEY or OPENAI_API_KEY in your .env configuration.")

def chunk_text(text_content: str, chunk_size: int = 1500, chunk_overlap: int = 200) -> List[str]:
    """
    Split text into overlapping chunks using RecursiveCharacterTextSplitter if possible,
    otherwise fallback to a custom character-based window.
    """
    try:
        # pyrefly: ignore [missing-import]
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )
        return splitter.split_text(text_content)
    except Exception as e:
        logger.debug(f"Langchain splitter import failed, using manual chunker: {e}")
        chunks = []
        start = 0
        text_len = len(text_content)
        while start < text_len:
            end = min(start + chunk_size, text_len)
            chunks.append(text_content[start:end])
            if end == text_len:
                break
            start += chunk_size - chunk_overlap
        return chunks

def add_document_to_store(db, project_id: str, name: str, file_path: str, file_type: str, content: str):
    """
    Chunks document content, calculates embeddings, and saves records to database.
    """
    chunks = chunk_text(content)
    embedder = get_embeddings_client()
    
    # Calculate embeddings
    embeddings = embedder.embed_documents(chunks)
    
    for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        doc_record = Document(
            project_id=project_id,
            name=f"{name}_part_{i+1}",
            file_path=file_path,
            file_type=file_type,
            content=chunk,
            embedding=emb
        )
        db.add(doc_record)
    
    db.commit()
    logger.info(f"Successfully indexed document '{name}' into {len(chunks)} chunks.")

def similarity_search(db, project_id: str, query: str, limit: int = 5) -> List[Tuple[Dict[str, Any], float]]:
    """
    Searches documents for a project using similarity distance metric.
    Adapts based on whether target DB is SQLite or PostgreSQL (Supabase).
    """
    embedder = get_embeddings_client()
    query_emb = embedder.embed_query(query)

    if is_sqlite:
        return _similarity_search_sqlite(db, project_id, query_emb, limit)
    else:
        return _similarity_search_postgres(db, project_id, query_emb, limit)

def _similarity_search_sqlite(db, project_id: str, query_emb: List[float], limit: int) -> List[Tuple[Dict[str, Any], float]]:
    docs = db.query(Document).filter(Document.project_id == project_id).all()
    if not docs:
        return []
    
    q_vec = np.array(query_emb)
    q_norm = np.linalg.norm(q_vec)
    if q_norm == 0:
        return []
        
    scores = []
    for doc in docs:
        if not doc.embedding:
            continue
        
        # doc.embedding might be returned as list or json parsed depending on SQLAlchemy SQLiteVector
        doc_emb = doc.embedding
        if isinstance(doc_emb, str):
            try:
                doc_emb = json.loads(doc_emb)
            except Exception:
                continue
                
        doc_vec = np.array(doc_emb)
        doc_norm = np.linalg.norm(doc_vec)
        if doc_norm == 0:
            continue
            
        sim = float(np.dot(q_vec, doc_vec) / (q_norm * doc_norm))
        doc_data = {
            "id": doc.id,
            "project_id": doc.project_id,
            "name": doc.name,
            "file_path": doc.file_path,
            "file_type": doc.file_type,
            "content": doc.content
        }
        scores.append((doc_data, sim))
        
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:limit]

def _similarity_search_postgres(db, project_id: str, query_emb: List[float], limit: int) -> List[Tuple[Dict[str, Any], float]]:
    # Execute pgvector raw cosine distance search
    # '<=>' in pgvector represents cosine distance (1 - cosine_similarity)
    sql = text("""
        SELECT id, name, file_path, file_type, content, project_id,
               (1.0 - (embedding <=> :query_emb)) as similarity
        FROM documents
        WHERE project_id = :project_id AND embedding IS NOT NULL
        ORDER BY embedding <=> :query_emb
        LIMIT :limit
    """)
    
    emb_str = "[" + ",".join(map(str, query_emb)) + "]"
    
    try:
        res = db.execute(sql, {"project_id": project_id, "query_emb": emb_str, "limit": limit}).fetchall()
        results = []
        for row in res:
            doc_data = {
                "id": str(row[0]),
                "name": row[1],
                "file_path": row[2],
                "file_type": row[3],
                "content": row[4],
                "project_id": str(row[5])
            }
            results.append((doc_data, float(row[6])))
        return results
    except Exception as e:
        logger.error(f"PostgreSQL pgvector query failed, running fallback Python similarity match: {e}")
        # Run SQL fallback in python in case extension is missing in Postgres
        docs = db.query(Document).filter(Document.project_id == project_id).all()
        scores = []
        q_vec = np.array(query_emb)
        q_norm = np.linalg.norm(q_vec)
        for doc in docs:
            if not doc.embedding:
                continue
            doc_vec = np.array(doc.embedding)
            doc_norm = np.linalg.norm(doc_vec)
            if doc_norm == 0 or q_norm == 0:
                continue
            sim = float(np.dot(q_vec, doc_vec) / (q_norm * doc_norm))
            doc_data = {
                "id": doc.id,
                "project_id": doc.project_id,
                "name": doc.name,
                "file_path": doc.file_path,
                "file_type": doc.file_type,
                "content": doc.content
            }
            scores.append((doc_data, sim))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:limit]
