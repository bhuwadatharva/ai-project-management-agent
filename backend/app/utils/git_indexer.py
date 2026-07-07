import os
import shutil
import tempfile
import logging
from git import Repo
from backend.app.rag.vector_store import add_document_to_store

logger = logging.getLogger(__name__)

# Extensions of source code files we want to parse
CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".go", 
    ".java", ".cpp", ".c", ".h", ".cs", ".json", ".yaml", ".yml", 
    ".md", ".txt", ".sql", ".sh", ".toml", ".ini"
}

# Directories to ignore
IGNORE_DIRS = {
    ".git", "node_modules", "venv", ".venv", "env", "__pycache__", 
    "dist", "build", "target", ".idea", ".vscode", "artifacts", "brain"
}

def clone_and_index_repository(db, project_id: str, repo_path_or_url: str) -> dict:
    """
    Clones a remote git repository or checks a local folder path,
    walks its file structure, indexes all source code documents.
    """
    temp_dir = None
    is_url = repo_path_or_url.startswith("http://") or repo_path_or_url.startswith("https://") or repo_path_or_url.startswith("git@")
    
    try:
        if is_url:
            temp_dir = tempfile.mkdtemp(prefix="devpilot_repo_")
            logger.info(f"Cloning remote repository {repo_path_or_url} to {temp_dir}...")
            # For remote cloning, we can fetch public repos. 
            # In a production environment, github tokens would be passed as credentials
            Repo.clone_from(repo_path_or_url, temp_dir)
            source_dir = temp_dir
        else:
            if not os.path.exists(repo_path_or_url):
                raise FileNotFoundError(f"Local repository path does not exist: {repo_path_or_url}")
            source_dir = repo_path_or_url
            logger.info(f"Indexing local repository from {source_dir}...")

        # Count total indexed files and folders
        indexed_files = 0
        file_tree = []

        # Traverse directory
        for root, dirs, files in os.walk(source_dir):
            # Modify dirs in-place to avoid traversing ignored folders
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in CODE_EXTENSIONS:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, source_dir)
                    
                    try:
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                            
                        # Add to file tree summary list
                        file_tree.append(rel_path)
                        
                        # Store code file content with parts into Vector DB
                        add_document_to_store(
                            db=db,
                            project_id=project_id,
                            name=f"code:{rel_path}",
                            file_path=rel_path,
                            file_type="code",
                            content=content
                        )
                        indexed_files += 1
                    except Exception as fe:
                        logger.warning(f"Failed to read/index code file {rel_path}: {fe}")

        # Also store the directory structure as a single meta-document for Supervisor/Repo agents
        if file_tree:
            tree_text = "Repository Project Structure:\n" + "\n".join(f"- {path}" for path in sorted(file_tree))
            add_document_to_store(
                db=db,
                project_id=project_id,
                name="repo_metadata:structure",
                file_path="PROJECT_STRUCTURE.md",
                file_type="code",
                content=tree_text
            )

        return {
            "status": "success",
            "indexed_files": indexed_files,
            "project_structure": file_tree
        }
        
    except Exception as e:
        logger.error(f"Error indexing repository {repo_path_or_url}: {e}")
        raise e
        
    finally:
        # Cleanup cloned directory if created
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                logger.info(f"Cleaned up temporary cloned repository folder {temp_dir}")
            except Exception as ce:
                logger.warning(f"Failed to cleanup temp directory {temp_dir}: {ce}")
