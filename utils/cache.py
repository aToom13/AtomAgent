"""
AtomAgent Caching System
Response caching for cost reduction and performance improvement
"""
import hashlib
import json
import os
import time
from typing import Any, Callable, Dict, Optional
from functools import wraps
from dataclasses import dataclass, field
from threading import Lock

from config import config
from utils.logger import get_logger

logger = get_logger()

CACHE_DIR = os.path.join(config.memory.checkpoint_dir, "cache")
os.makedirs(CACHE_DIR, exist_ok=True)


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    value: Any
    created_at: float
    ttl: float
    hits: int = 0
    
    def is_expired(self) -> bool:
        return time.time() - self.created_at > self.ttl
    
    def to_dict(self) -> dict:
        return {
            "value": self.value,
            "created_at": self.created_at,
            "ttl": self.ttl,
            "hits": self.hits
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'CacheEntry':
        return CacheEntry(
            value=data["value"],
            created_at=data["created_at"],
            ttl=data["ttl"],
            hits=data.get("hits", 0)
        )


class ResponseCache:
    """
    LRU Cache with TTL for LLM responses.
    Reduces API costs by caching similar queries.
    """
    
    def __init__(self, max_size: int = 500, default_ttl: float = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, CacheEntry] = {}
        self.lock = Lock()
        self._load_persistent_cache()
    
    def _generate_key(self, query: str, context: str = "") -> str:
        """Generate cache key from query and context"""
        content = f"{query}:{context}"
        return hashlib.sha256(content.encode()).hexdigest()[:32]
    
    def _load_persistent_cache(self):
        """Load cache from disk"""
        cache_file = os.path.join(CACHE_DIR, "response_cache.json")
        try:
            if os.path.exists(cache_file):
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for key, entry_data in data.items():
                        entry = CacheEntry.from_dict(entry_data)
                        if not entry.is_expired():
                            self.cache[key] = entry
                logger.info(f"Loaded {len(self.cache)} cached responses")
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
    
    def _save_persistent_cache(self):
        """Save cache to disk"""
        cache_file = os.path.join(CACHE_DIR, "response_cache.json")
        try:
            # Only save non-expired entries
            data = {
                k: v.to_dict() 
                for k, v in self.cache.items() 
                if not v.is_expired()
            }
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")
    
    def get(self, query: str, context: str = "") -> Optional[Any]:
        """Get cached response if exists and not expired"""
        key = self._generate_key(query, context)
        
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                if not entry.is_expired():
                    entry.hits += 1
                    logger.debug(f"Cache hit for query: {query[:50]}...")
                    return entry.value
                else:
                    del self.cache[key]
        
        return None
    
    def set(self, query: str, value: Any, context: str = "", ttl: float = None):
        """Cache a response"""
        key = self._generate_key(query, context)
        ttl = ttl or self.default_ttl
        
        with self.lock:
            # Evict oldest entries if at capacity
            if len(self.cache) >= self.max_size:
                self._evict_oldest()
            
            self.cache[key] = CacheEntry(
                value=value,
                created_at=time.time(),
                ttl=ttl
            )
            
            # Periodically save to disk
            if len(self.cache) % 50 == 0:
                self._save_persistent_cache()
    
    def _evict_oldest(self):
        """Remove oldest entries to make room"""
        if not self.cache:
            return
        
        # Sort by created_at and remove oldest 10%
        sorted_keys = sorted(
            self.cache.keys(),
            key=lambda k: self.cache[k].created_at
        )
        
        to_remove = max(1, len(sorted_keys) // 10)
        for key in sorted_keys[:to_remove]:
            del self.cache[key]
    
    def get_or_compute(self, query: str, compute_fn: Callable, 
                       context: str = "", ttl: float = None) -> Any:
        """Get from cache or compute and cache result"""
        cached = self.get(query, context)
        if cached is not None:
            return cached
        
        result = compute_fn()
        self.set(query, result, context, ttl)
        return result
    
    def invalidate(self, query: str, context: str = ""):
        """Invalidate a specific cache entry"""
        key = self._generate_key(query, context)
        with self.lock:
            if key in self.cache:
                del self.cache[key]
    
    def clear(self):
        """Clear all cache"""
        with self.lock:
            self.cache.clear()
            self._save_persistent_cache()
        logger.info("Cache cleared")
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        with self.lock:
            total_hits = sum(e.hits for e in self.cache.values())
            expired = sum(1 for e in self.cache.values() if e.is_expired())
            
            return {
                "total_entries": len(self.cache),
                "expired_entries": expired,
                "total_hits": total_hits,
                "max_size": self.max_size,
                "default_ttl": self.default_ttl
            }


# Global cache instance
_response_cache = ResponseCache()


def get_cache() -> ResponseCache:
    """Get global cache instance"""
    return _response_cache


def cached_llm_call(ttl: float = 3600):
    """
    Decorator for caching LLM calls.
    
    Usage:
        @cached_llm_call(ttl=1800)
        def my_llm_function(query: str) -> str:
            return llm.invoke(query)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
            
            cached = _response_cache.get(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached
            
            result = func(*args, **kwargs)
            _response_cache.set(cache_key, result, ttl=ttl)
            return result
        
        return wrapper
    return decorator


class EmbeddingCache:
    """
    Specialized cache for embeddings.
    Embeddings are expensive to compute, so we cache them aggressively.
    """
    
    def __init__(self, cache_file: str = "embeddings_cache.json"):
        self.cache_file = os.path.join(CACHE_DIR, cache_file)
        self.cache: Dict[str, list] = {}
        self.lock = Lock()
        self._load()
    
    def _load(self):
        """Load embeddings from disk"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self.cache = json.load(f)
                logger.info(f"Loaded {len(self.cache)} cached embeddings")
        except Exception as e:
            logger.warning(f"Failed to load embeddings cache: {e}")
    
    def _save(self):
        """Save embeddings to disk"""
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.cache, f)
        except Exception as e:
            logger.warning(f"Failed to save embeddings cache: {e}")
    
    def get(self, text: str) -> Optional[list]:
        """Get cached embedding"""
        key = hashlib.md5(text.encode()).hexdigest()
        return self.cache.get(key)
    
    def set(self, text: str, embedding: list):
        """Cache an embedding"""
        key = hashlib.md5(text.encode()).hexdigest()
        with self.lock:
            self.cache[key] = embedding
            
            # Save periodically
            if len(self.cache) % 100 == 0:
                self._save()
    
    def get_or_compute(self, text: str, compute_fn: Callable) -> list:
        """Get from cache or compute"""
        cached = self.get(text)
        if cached is not None:
            return cached
        
        embedding = compute_fn()
        self.set(text, embedding)
        return embedding


# Global embedding cache
_embedding_cache = EmbeddingCache()


def get_embedding_cache() -> EmbeddingCache:
    """Get global embedding cache"""
    return _embedding_cache
