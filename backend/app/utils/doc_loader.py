import os
import pypdf
import docx
import logging

logger = logging.getLogger(__name__)

def load_document(file_path: str) -> str:
    """
    Load content of a document based on its file extension.
    Supported types: .pdf, .docx, .md, .txt
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
        
    ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if ext == ".pdf":
            return load_pdf(file_path)
        elif ext == ".docx":
            return load_docx(file_path)
        elif ext in [".md", ".txt"]:
            return load_text(file_path)
        else:
            # Fallback to text load for unknown types
            return load_text(file_path)
    except Exception as e:
        logger.error(f"Error loading document {file_path}: {e}")
        raise ValueError(f"Failed to parse {ext} file: {e}")

def load_pdf(file_path: str) -> str:
    text_content = []
    with open(file_path, "rb") as f:
        reader = pypdf.PdfReader(f)
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text = page.extract_text()
            if text:
                text_content.append(text)
    return "\n\n".join(text_content)

def load_docx(file_path: str) -> str:
    doc = docx.Document(file_path)
    text_content = []
    for para in doc.paragraphs:
        if para.text:
            text_content.append(para.text)
    return "\n".join(text_content)

def load_text(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()
