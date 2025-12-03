"""
Tests for utility modules
"""
import pytest
import time
from unittest.mock import MagicMock


class TestCache:
    """Test caching system"""
    
    def test_cache_set_and_get(self):
        """Test basic cache operations"""
        from utils.cache import ResponseCache
        
        cache = ResponseCache(max_size=100, default_ttl=3600)
        
        # Set value
        cache.set("test query", "test result")
        
        # Get value
        result = cache.get("test query")
        assert result == "test result"
    
    def test_cache_expiration(self):
        """Test cache expiration"""
        from utils.cache import ResponseCache
        
        cache = ResponseCache(max_size=100, default_ttl=0.1)  # 100ms TTL
        
        cache.set("test query", "test result")
        
        # Should exist immediately
        assert cache.get("test query") == "test result"
        
        # Wait for expiration
        time.sleep(0.2)
        
        # Should be expired
        assert cache.get("test query") is None
    
    def test_cache_get_or_compute(self):
        """Test get_or_compute functionality"""
        from utils.cache import ResponseCache
        
        cache = ResponseCache()
        compute_count = [0]
        
        def compute():
            compute_count[0] += 1
            return "computed result"
        
        # First call should compute
        result1 = cache.get_or_compute("query", compute)
        assert result1 == "computed result"
        assert compute_count[0] == 1
        
        # Second call should use cache
        result2 = cache.get_or_compute("query", compute)
        assert result2 == "computed result"
        assert compute_count[0] == 1  # Not incremented
    
    def test_cache_stats(self):
        """Test cache statistics"""
        from utils.cache import ResponseCache
        
        cache = ResponseCache()
        cache.set("q1", "r1")
        cache.set("q2", "r2")
        cache.get("q1")
        cache.get("q1")
        
        stats = cache.get_stats()
        assert stats["total_entries"] == 2
        assert stats["total_hits"] >= 2


class TestTelemetry:
    """Test telemetry and tracing"""
    
    def test_trace_span(self):
        """Test trace span creation"""
        from utils.telemetry import Tracer
        
        tracer = Tracer()
        
        with tracer.trace_span("test_operation") as span:
            span.set_attribute("key", "value")
            time.sleep(0.01)
        
        summary = tracer.get_trace_summary()
        assert summary["total_spans"] >= 1
    
    def test_trace_tool_call(self):
        """Test tool call tracing"""
        from utils.telemetry import trace_tool_call
        
        with trace_tool_call("test_tool", {"param": "value"}):
            pass  # Simulated tool execution
    
    def test_performance_monitor(self):
        """Test performance monitoring"""
        from utils.telemetry import PerformanceMonitor
        
        monitor = PerformanceMonitor()
        
        monitor.record_metric("response_time", 100.0)
        monitor.record_metric("response_time", 150.0)
        monitor.increment_counter("requests", 1)
        
        stats = monitor.get_metric_stats("response_time")
        assert stats["count"] == 2
        assert stats["avg"] == 125.0


class TestContextManager:
    """Test context window management"""
    
    def test_token_counting(self):
        """Test token counting"""
        from utils.context_manager import ContextWindowManager
        
        manager = ContextWindowManager()
        
        # Simple text
        count = manager.count_tokens("Hello world")
        assert count > 0
        assert count < 10
    
    def test_needs_compression(self):
        """Test compression detection"""
        from utils.context_manager import ContextWindowManager
        from langchain_core.messages import HumanMessage
        
        manager = ContextWindowManager(max_tokens=100, reserve_tokens=20)
        
        # Short messages - no compression needed
        short_messages = [HumanMessage(content="Hi")]
        assert not manager.needs_compression(short_messages)
        
        # Long messages - compression needed
        long_messages = [HumanMessage(content="x" * 1000)]
        assert manager.needs_compression(long_messages)
    
    def test_truncate_tool_output(self):
        """Test tool output truncation"""
        from utils.context_manager import ContextWindowManager
        
        manager = ContextWindowManager()
        
        # Short output - no truncation
        short = "Short output"
        assert manager.truncate_tool_output(short) == short
        
        # Long output - should be truncated
        long = "x" * 10000
        truncated = manager.truncate_tool_output(long, max_tokens=100)
        assert len(truncated) < len(long)
        assert "truncated" in truncated.lower()
