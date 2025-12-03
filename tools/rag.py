"""
RAG (Retrieval-Augmented Generation) Module
Vector-based semantic search for codebase understanding
"""
import os
from typing import List
from langchain_core.tools import tool
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from config import config
from utils.logger import get_logger

logger = get_logger()

WORKSPACE_DIR = config.workspace.base_dir
RAG_DB_PATH = os.path.join(WORKSPACE_DIR, ".rag_db")

# Supported file extensions
SUPPORTED_EXTENSIONS = {".py", ".md", ".js", ".ts", ".html", ".css", ".json", ".yaml", ".yml", ".txt"}

# Lazy-loaded components
_vectorstore = None
_embeddings = None


def _get_embeddings():
    """Lazy load embeddings model"""
    global _embeddings
    if _embeddings is None:
        try:
            from langchain_ollama import OllamaEmbeddings
            _embeddings = OllamaEmbeddings(model="nomic-embed-text")
            logger.info("Embeddings model loaded: nomic-embed-text")
        except Exception as e:
            logger.error(f"Failed to load embeddings: {e}")
            raise
    return _embeddings


def _get_vectorstore(create_if_missing: bool = True):
    """Lazy load or create vector store"""
    global _vectorstore
    if _vectorstore is None:
        try:
            from langchain_chroma import Chroma
            
            os.makedirs(RAG_DB_PATH, exist_ok=True)
            
            _vectorstore = Chroma(
                persist_directory=RAG_DB_PATH,
                embedding_function=_get_embeddings(),
                collection_name="codebase"
            )
            logger.info(f"Vector store initialized at {RAG_DB_PATH}")
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise
    return _vectorstore


def _scan_files(directory: str) -> List[str]:
    """Recursively scan directory for supported files"""
    files = []
    for root, _, filenames in os.walk(directory):
        # Skip hidden directories and rag_db
        if any(part.startswith('.') for part in root.split(os.sep)):
            continue
        
        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()
            if ext in SUPPORTED_EXTENSIONS:
                files.append(os.path.join(root, filename))
    
    return files


def _load_documents(files: List[str]) -> List[Document]:
    """Load and split documents from files"""
    documents = []
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""]
    )
    
    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            
            if not content.strip():
                continue
            
            # Get relative path for metadata
            rel_path = os.path.relpath(file_path, WORKSPACE_DIR)
            
            # Split content into chunks
            chunks = splitter.split_text(content)
            
            for i, chunk in enumerate(chunks):
                doc = Document(
                    page_content=chunk,
                    metadata={
                        "source": rel_path,
                        "chunk_index": i,
                        "file_type": os.path.splitext(file_path)[1]
                    }
                )
                documents.append(doc)
                
        except Exception as e:
            logger.warning(f"Failed to load {file_path}: {e}")
    
    return documents


@tool
def refresh_memory() -> str:
    """
    Scans the workspace and updates the vector memory with all code files.
    Call this after making significant changes to the codebase.
    Indexes: .py, .md, .js, .ts, .html, .css, .json, .yaml files
    
    Returns:
        Status message with number of documents indexed
    """
    logger.info("Refreshing RAG memory...")
    
    try:
        # Scan files
        files = _scan_files(WORKSPACE_DIR)
        
        if not files:
            return "No files found in workspace to index."
        
        # Load and split documents
        documents = _load_documents(files)
        
        if not documents:
            return "No content found to index."
        
        # Get or create vector store
        vectorstore = _get_vectorstore()
        
        # Clear existing data and add new
        try:
            # Delete existing collection
            vectorstore.delete_collection()
        except:
            pass
        
        # Recreate with new documents
        global _vectorstore
        from langchain_chroma import Chroma
        
        _vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=_get_embeddings(),
            persist_directory=RAG_DB_PATH,
            collection_name="codebase"
        )
        
        logger.info(f"RAG memory refreshed: {len(documents)} chunks from {len(files)} files")
        return f"Memory refreshed: {len(documents)} chunks indexed from {len(files)} files."
        
    except Exception as e:
        logger.error(f"Failed to refresh memory: {e}")
        return f"Error refreshing memory: {e}"


def _keyword_search(query: str, limit: int = 3) -> List[Document]:
    """Simple keyword search implementation"""
    results = []
    query_lower = query.lower()
    files = _scan_files(WORKSPACE_DIR)
    
    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            
            if query_lower in content.lower():
                # Find the line with the match
                lines = content.splitlines()
                for i, line in enumerate(lines):
                    if query_lower in line.lower():
                        # Extract context (3 lines before and after)
                        start = max(0, i - 2)
                        end = min(len(lines), i + 3)
                        snippet = "\n".join(lines[start:end])
                        
                        rel_path = os.path.relpath(file_path, WORKSPACE_DIR)
                        results.append(Document(
                            page_content=snippet,
                            metadata={"source": rel_path, "type": "keyword"}
                        ))
                        break # One snippet per file for now
        except:
            continue
            
    return results[:limit]


@tool
def search_codebase(query: str) -> str:
    """
    Searches the codebase using Hybrid Search (Vector + Keyword).
    Combines semantic similarity with exact keyword matching for better results.
    
    Args:
        query: Natural language description or specific keywords
    
    Returns:
        Relevant code snippets with file paths
    """
    logger.info(f"Searching codebase (Hybrid): {query[:50]}...")
    
    try:
        results = []
        seen_sources = set()
        
        # 1. Vector Search (Semantic)
        try:
            vectorstore = _get_vectorstore()
            vector_results = vectorstore.similarity_search(query, k=3)
            for doc in vector_results:
                doc.metadata["type"] = "semantic"
                results.append(doc)
                seen_sources.add(doc.metadata.get("source"))
        except Exception as e:
            logger.warning(f"Vector search failed: {e}")
        
        # 2. Keyword Search (Exact)
        # Only if query is short enough to be a keyword/phrase
        if len(query.split()) < 5:
            keyword_results = _keyword_search(query, limit=3)
            for doc in keyword_results:
                # Avoid duplicates if possible (simple check)
                if doc.metadata.get("source") not in seen_sources:
                    results.append(doc)
        
        if not results:
            return f"No relevant code found for: {query}. Try running refresh_memory() if this is unexpected."
        
        # Format results
        output_parts = [f"🔍 Search Results for '{query}':\n"]
        
        for doc in results:
            source = doc.metadata.get("source", "unknown")
            match_type = doc.metadata.get("type", "unknown")
            icon = "🧠" if match_type == "semantic" else "🔑"
            
            output_parts.append(f"\n{icon} {source} ({match_type}):")
            
            # Add code snippet (truncated if too long)
            content = doc.page_content
            if len(content) > 500:
                content = content[:500] + "..."
            
            output_parts.append(f"```\n{content}\n```")
        
        result = "\n".join(output_parts)
        return result
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return f"Search error: {e}"
