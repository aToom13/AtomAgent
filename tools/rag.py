"""
RAG (Retrieval-Augmented Generation) Module
Hybrid Search: Vector + Keyword + Reranking
Enhanced for better code understanding
"""
import os
import re
from typing import List, Tuple, Optional
from langchain_core.tools import tool
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from config import config
from utils.logger import get_logger

logger = get_logger()

WORKSPACE_DIR = config.workspace.base_dir
RAG_DB_PATH = os.path.join(WORKSPACE_DIR, ".rag_db")

# Supported file extensions with weights
SUPPORTED_EXTENSIONS = {
    ".py": 1.0, ".js": 1.0, ".ts": 1.0,  # High priority
    ".md": 0.8, ".txt": 0.7,  # Documentation
    ".html": 0.6, ".css": 0.5,  # Frontend
    ".json": 0.5, ".yaml": 0.5, ".yml": 0.5  # Config
}

# Lazy-loaded components
_vectorstore = None
_embeddings = None
_reranker = None


def _get_embeddings():
    """Lazy load embeddings model with caching support"""
    global _embeddings
    if _embeddings is None:
        try:
            from langchain_ollama import OllamaEmbeddings
            _embeddings = CachedEmbeddings(OllamaEmbeddings(model="nomic-embed-text"))
            logger.info("Embeddings model loaded: nomic-embed-text (cached)")
        except Exception as e:
            logger.error(f"Failed to load embeddings: {e}")
            raise
    return _embeddings


class CachedEmbeddings:
    """Wrapper for embeddings with caching"""
    
    def __init__(self, base_embeddings):
        self.base = base_embeddings
        try:
            from utils.cache import get_embedding_cache
            self.cache = get_embedding_cache()
        except:
            self.cache = None
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed documents with caching"""
        results = []
        uncached_texts = []
        uncached_indices = []
        
        for i, text in enumerate(texts):
            if self.cache:
                cached = self.cache.get(text)
                if cached:
                    results.append(cached)
                    continue
            uncached_texts.append(text)
            uncached_indices.append(i)
            results.append(None)
        
        if uncached_texts:
            new_embeddings = self.base.embed_documents(uncached_texts)
            for idx, emb in zip(uncached_indices, new_embeddings):
                results[idx] = emb
                if self.cache:
                    self.cache.set(texts[idx], emb)
        
        return results
    
    def embed_query(self, text: str) -> List[float]:
        """Embed query with caching"""
        if self.cache:
            cached = self.cache.get(text)
            if cached:
                return cached
        
        embedding = self.base.embed_query(text)
        if self.cache:
            self.cache.set(text, embedding)
        return embedding


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


def _get_reranker():
    """Get reranker model (optional, for better results)"""
    global _reranker
    if _reranker is None:
        try:
            # Try to load cross-encoder for reranking
            from sentence_transformers import CrossEncoder
            _reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
            logger.info("Reranker loaded: ms-marco-MiniLM-L-6-v2")
        except ImportError:
            logger.debug("sentence-transformers not installed, reranking disabled")
            _reranker = False  # Mark as unavailable
        except Exception as e:
            logger.warning(f"Failed to load reranker: {e}")
            _reranker = False
    return _reranker if _reranker else None


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


def _extract_code_elements(content: str, file_type: str) -> dict:
    """Extract code elements for better indexing"""
    elements = {
        "functions": [],
        "classes": [],
        "imports": [],
        "comments": []
    }
    
    if file_type == ".py":
        # Extract Python elements
        elements["functions"] = re.findall(r'def\s+(\w+)\s*\(', content)
        elements["classes"] = re.findall(r'class\s+(\w+)\s*[:\(]', content)
        elements["imports"] = re.findall(r'(?:from|import)\s+([\w.]+)', content)
    elif file_type in [".js", ".ts"]:
        # Extract JS/TS elements
        elements["functions"] = re.findall(r'(?:function|const|let|var)\s+(\w+)\s*[=\(]', content)
        elements["classes"] = re.findall(r'class\s+(\w+)', content)
        elements["imports"] = re.findall(r'import\s+.*?from\s+[\'"](.+?)[\'"]', content)
    
    return elements


def _load_documents(files: List[str]) -> List[Document]:
    """Load and split documents from files with enhanced metadata"""
    documents = []
    
    # Use code-aware splitter with more overlap
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,  # Slightly larger chunks
        chunk_overlap=300,  # More overlap for context
        separators=[
            "\n\nclass ", "\n\ndef ", "\n\nasync def ",  # Python
            "\n\nfunction ", "\n\nconst ", "\n\nexport ",  # JS
            "\n\n## ", "\n\n# ",  # Markdown
            "\n\n", "\n", " ", ""
        ]
    )
    
    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            
            if not content.strip():
                continue
            
            # Get relative path and file type
            rel_path = os.path.relpath(file_path, WORKSPACE_DIR)
            file_type = os.path.splitext(file_path)[1].lower()
            
            # Extract code elements
            elements = _extract_code_elements(content, file_type)
            
            # Calculate file weight
            weight = SUPPORTED_EXTENSIONS.get(file_type, 0.5)
            
            # Split content into chunks
            chunks = splitter.split_text(content)
            
            for i, chunk in enumerate(chunks):
                # Find which functions/classes are in this chunk
                chunk_functions = [f for f in elements["functions"] if f in chunk]
                chunk_classes = [c for c in elements["classes"] if c in chunk]
                
                doc = Document(
                    page_content=chunk,
                    metadata={
                        "source": rel_path,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "file_type": file_type,
                        "weight": weight,
                        "functions": chunk_functions[:5],  # Limit to 5
                        "classes": chunk_classes[:3],
                        "has_code": bool(chunk_functions or chunk_classes)
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


def _keyword_search(query: str, limit: int = 5) -> List[Tuple[Document, float]]:
    """Enhanced keyword search with scoring"""
    results = []
    query_lower = query.lower()
    query_words = set(query_lower.split())
    files = _scan_files(WORKSPACE_DIR)
    
    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            
            content_lower = content.lower()
            
            # Calculate relevance score
            score = 0.0
            
            # Exact phrase match (highest score)
            if query_lower in content_lower:
                score += 1.0
            
            # Word matches
            for word in query_words:
                if len(word) > 2:  # Skip short words
                    count = content_lower.count(word)
                    score += min(count * 0.1, 0.5)  # Cap at 0.5 per word
            
            if score > 0:
                # Find best matching snippet
                lines = content.splitlines()
                best_snippet = None
                best_line_score = 0
                
                for i, line in enumerate(lines):
                    line_lower = line.lower()
                    line_score = sum(1 for w in query_words if w in line_lower)
                    
                    if line_score > best_line_score:
                        best_line_score = line_score
                        start = max(0, i - 3)
                        end = min(len(lines), i + 4)
                        best_snippet = "\n".join(lines[start:end])
                
                if best_snippet:
                    rel_path = os.path.relpath(file_path, WORKSPACE_DIR)
                    file_type = os.path.splitext(file_path)[1].lower()
                    weight = SUPPORTED_EXTENSIONS.get(file_type, 0.5)
                    
                    doc = Document(
                        page_content=best_snippet,
                        metadata={
                            "source": rel_path,
                            "type": "keyword",
                            "file_type": file_type
                        }
                    )
                    results.append((doc, score * weight))
        except:
            continue
    
    # Sort by score and return top results
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:limit]


def _rerank_results(query: str, documents: List[Document], top_k: int = 5) -> List[Document]:
    """Rerank results using cross-encoder"""
    reranker = _get_reranker()
    
    if not reranker or len(documents) <= top_k:
        return documents[:top_k]
    
    try:
        # Prepare pairs for reranking
        pairs = [(query, doc.page_content) for doc in documents]
        
        # Get scores
        scores = reranker.predict(pairs)
        
        # Sort by score
        scored_docs = list(zip(documents, scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        logger.debug(f"Reranked {len(documents)} documents")
        return [doc for doc, _ in scored_docs[:top_k]]
    
    except Exception as e:
        logger.warning(f"Reranking failed: {e}")
        return documents[:top_k]


@tool
def search_codebase(query: str) -> str:
    """
    Searches the codebase using Hybrid Search (Vector + Keyword + Reranking).
    Combines semantic similarity with exact keyword matching for best results.
    
    Args:
        query: Natural language description or specific keywords
    
    Returns:
        Relevant code snippets with file paths
    """
    logger.info(f"Searching codebase (Hybrid): {query[:50]}...")
    
    try:
        all_results = []
        seen_content = set()
        
        # 1. Vector Search (Semantic)
        try:
            vectorstore = _get_vectorstore()
            vector_results = vectorstore.similarity_search_with_score(query, k=5)
            
            for doc, score in vector_results:
                content_hash = hash(doc.page_content[:100])
                if content_hash not in seen_content:
                    doc.metadata["type"] = "semantic"
                    doc.metadata["score"] = 1.0 - min(score, 1.0)  # Convert distance to similarity
                    all_results.append(doc)
                    seen_content.add(content_hash)
        except Exception as e:
            logger.warning(f"Vector search failed: {e}")
        
        # 2. Keyword Search (Exact)
        keyword_results = _keyword_search(query, limit=5)
        for doc, score in keyword_results:
            content_hash = hash(doc.page_content[:100])
            if content_hash not in seen_content:
                doc.metadata["score"] = score
                all_results.append(doc)
                seen_content.add(content_hash)
        
        if not all_results:
            return f"No relevant code found for: {query}. Try running refresh_memory() if this is unexpected."
        
        # 3. Rerank results
        reranked = _rerank_results(query, all_results, top_k=5)
        
        # Format results
        output_parts = [f"🔍 Search Results for '{query}':\n"]
        
        for i, doc in enumerate(reranked, 1):
            source = doc.metadata.get("source", "unknown")
            match_type = doc.metadata.get("type", "unknown")
            functions = doc.metadata.get("functions", [])
            classes = doc.metadata.get("classes", [])
            
            icon = "🧠" if match_type == "semantic" else "🔑"
            
            # Build header
            header = f"\n{icon} [{i}] {source}"
            if functions:
                header += f" (functions: {', '.join(functions[:3])})"
            if classes:
                header += f" (classes: {', '.join(classes[:2])})"
            
            output_parts.append(header)
            
            # Add code snippet (truncated if too long)
            content = doc.page_content
            if len(content) > 600:
                content = content[:600] + "\n...[truncated]..."
            
            output_parts.append(f"```\n{content}\n```")
        
        result = "\n".join(output_parts)
        return result
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return f"Search error: {e}"


@tool
def search_functions(function_name: str) -> str:
    """
    Search for a specific function or class in the codebase.
    More precise than general search for finding definitions.
    
    Args:
        function_name: Name of the function or class to find
    
    Returns:
        Function/class definition with context
    """
    logger.info(f"Searching for function/class: {function_name}")
    
    files = _scan_files(WORKSPACE_DIR)
    results = []
    
    # Patterns to match
    patterns = [
        rf'def\s+{re.escape(function_name)}\s*\(',  # Python function
        rf'class\s+{re.escape(function_name)}\s*[:\(]',  # Python class
        rf'function\s+{re.escape(function_name)}\s*\(',  # JS function
        rf'const\s+{re.escape(function_name)}\s*=',  # JS const
        rf'class\s+{re.escape(function_name)}\s*\{{',  # JS class
    ]
    
    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            
            for pattern in patterns:
                match = re.search(pattern, content)
                if match:
                    # Extract context around match
                    lines = content.splitlines()
                    for i, line in enumerate(lines):
                        if re.search(pattern, line):
                            start = max(0, i - 2)
                            end = min(len(lines), i + 20)  # More context for definitions
                            snippet = "\n".join(lines[start:end])
                            
                            rel_path = os.path.relpath(file_path, WORKSPACE_DIR)
                            results.append({
                                "source": rel_path,
                                "line": i + 1,
                                "snippet": snippet
                            })
                            break
                    break
        except:
            continue
    
    if not results:
        return f"Function/class '{function_name}' not found in codebase."
    
    output_parts = [f"📍 Found '{function_name}':\n"]
    
    for r in results[:3]:  # Max 3 results
        output_parts.append(f"\n📄 {r['source']} (line {r['line']}):")
        output_parts.append(f"```\n{r['snippet']}\n```")
    
    return "\n".join(output_parts)
