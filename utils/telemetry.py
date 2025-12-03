"""
AtomAgent Telemetry & Observability
Tool call tracing, performance monitoring, and debugging support
"""
import time
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from contextlib import contextmanager
from functools import wraps
from dataclasses import dataclass, field
from threading import Lock

from config import config
from utils.logger import get_logger

logger = get_logger()

TELEMETRY_DIR = os.path.join(config.memory.checkpoint_dir, "telemetry")
os.makedirs(TELEMETRY_DIR, exist_ok=True)


@dataclass
class TraceSpan:
    """A single trace span representing an operation"""
    name: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    status: str = "running"
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict] = field(default_factory=list)
    parent_id: Optional[str] = None
    span_id: str = field(default_factory=lambda: f"{time.time_ns()}")
    
    def finish(self, status: str = "success"):
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self.status = status
    
    def add_event(self, name: str, attributes: Dict = None):
        self.events.append({
            "name": name,
            "timestamp": time.time(),
            "attributes": attributes or {}
        })
    
    def set_attribute(self, key: str, value: Any):
        self.attributes[key] = value
    
    def to_dict(self) -> dict:
        return {
            "span_id": self.span_id,
            "name": self.name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "attributes": self.attributes,
            "events": self.events,
            "parent_id": self.parent_id
        }


class Tracer:
    """
    Distributed tracing for tool calls and agent operations.
    Helps debug complex multi-step operations.
    """
    
    def __init__(self, service_name: str = "AtomAgent"):
        self.service_name = service_name
        self.active_spans: Dict[str, TraceSpan] = {}
        self.completed_spans: List[TraceSpan] = []
        self.current_trace_id: Optional[str] = None
        self.lock = Lock()
        self._span_stack: List[str] = []
    
    def start_trace(self, name: str = "request") -> str:
        """Start a new trace"""
        self.current_trace_id = f"trace_{time.time_ns()}"
        logger.debug(f"Started trace: {self.current_trace_id}")
        return self.current_trace_id
    
    def start_span(self, name: str, attributes: Dict = None) -> TraceSpan:
        """Start a new span"""
        parent_id = self._span_stack[-1] if self._span_stack else None
        
        span = TraceSpan(
            name=name,
            start_time=time.time(),
            attributes=attributes or {},
            parent_id=parent_id
        )
        
        with self.lock:
            self.active_spans[span.span_id] = span
            self._span_stack.append(span.span_id)
        
        logger.debug(f"🔧 {name} started")
        return span
    
    def end_span(self, span: TraceSpan, status: str = "success"):
        """End a span"""
        span.finish(status)
        
        with self.lock:
            if span.span_id in self.active_spans:
                del self.active_spans[span.span_id]
            if span.span_id in self._span_stack:
                self._span_stack.remove(span.span_id)
            self.completed_spans.append(span)
        
        status_icon = "✅" if status == "success" else "❌"
        logger.debug(f"{status_icon} {span.name} completed in {span.duration_ms:.2f}ms")
    
    @contextmanager
    def trace_span(self, name: str, attributes: Dict = None):
        """Context manager for tracing a span"""
        span = self.start_span(name, attributes)
        try:
            yield span
            self.end_span(span, "success")
        except Exception as e:
            span.set_attribute("error", str(e))
            self.end_span(span, "error")
            raise
    
    def get_trace_summary(self) -> Dict:
        """Get summary of current trace"""
        total_duration = sum(
            s.duration_ms or 0 
            for s in self.completed_spans
        )
        
        return {
            "trace_id": self.current_trace_id,
            "total_spans": len(self.completed_spans),
            "active_spans": len(self.active_spans),
            "total_duration_ms": total_duration,
            "spans": [s.to_dict() for s in self.completed_spans[-20:]]
        }
    
    def export_trace(self, filename: str = None):
        """Export trace to file"""
        if not filename:
            filename = f"trace_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = os.path.join(TELEMETRY_DIR, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.get_trace_summary(), f, indent=2, ensure_ascii=False)
        
        logger.info(f"Trace exported to {filepath}")
        return filepath
    
    def clear(self):
        """Clear all spans"""
        with self.lock:
            self.active_spans.clear()
            self.completed_spans.clear()
            self._span_stack.clear()
            self.current_trace_id = None


# Global tracer instance
_tracer = Tracer()


def get_tracer() -> Tracer:
    """Get global tracer instance"""
    return _tracer


@contextmanager
def trace_tool_call(tool_name: str, params: Dict = None):
    """
    Context manager for tracing tool calls.
    
    Usage:
        with trace_tool_call("write_file", {"path": "test.py"}):
            # tool implementation
    """
    tracer = get_tracer()
    with tracer.trace_span(f"tool:{tool_name}", {"params": params or {}}):
        yield


def traced_tool(func: Callable) -> Callable:
    """
    Decorator for automatically tracing tool calls.
    
    Usage:
        @traced_tool
        def my_tool(arg1: str) -> str:
            return "result"
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        tool_name = func.__name__
        params = {"args": str(args)[:100], "kwargs": str(kwargs)[:100]}
        
        with trace_tool_call(tool_name, params) as span:
            try:
                result = func(*args, **kwargs)
                span.set_attribute("result_length", len(str(result)))
                return result
            except Exception as e:
                span.set_attribute("error", str(e))
                raise
    
    return wrapper


class PerformanceMonitor:
    """
    Monitors performance metrics for the agent.
    Tracks response times, token usage, and resource consumption.
    """
    
    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}
        self.counters: Dict[str, int] = {}
        self.lock = Lock()
    
    def record_metric(self, name: str, value: float):
        """Record a metric value"""
        with self.lock:
            if name not in self.metrics:
                self.metrics[name] = []
            self.metrics[name].append(value)
            
            # Keep only last 1000 values
            if len(self.metrics[name]) > 1000:
                self.metrics[name] = self.metrics[name][-1000:]
    
    def increment_counter(self, name: str, value: int = 1):
        """Increment a counter"""
        with self.lock:
            self.counters[name] = self.counters.get(name, 0) + value
    
    def get_metric_stats(self, name: str) -> Dict:
        """Get statistics for a metric"""
        values = self.metrics.get(name, [])
        if not values:
            return {"count": 0}
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "last": values[-1]
        }
    
    def get_all_stats(self) -> Dict:
        """Get all metrics and counters"""
        return {
            "metrics": {
                name: self.get_metric_stats(name)
                for name in self.metrics
            },
            "counters": dict(self.counters)
        }
    
    def reset(self):
        """Reset all metrics"""
        with self.lock:
            self.metrics.clear()
            self.counters.clear()


# Global performance monitor
_perf_monitor = PerformanceMonitor()


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor"""
    return _perf_monitor


def record_response_time(operation: str, duration_ms: float):
    """Record response time for an operation"""
    _perf_monitor.record_metric(f"response_time:{operation}", duration_ms)


def record_token_usage(input_tokens: int, output_tokens: int):
    """Record token usage"""
    _perf_monitor.increment_counter("total_input_tokens", input_tokens)
    _perf_monitor.increment_counter("total_output_tokens", output_tokens)
    _perf_monitor.increment_counter("total_requests", 1)


def timed_operation(operation_name: str):
    """
    Decorator for timing operations.
    
    Usage:
        @timed_operation("database_query")
        def query_db():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                duration_ms = (time.time() - start) * 1000
                record_response_time(operation_name, duration_ms)
        return wrapper
    return decorator


class DebugContext:
    """
    Debug context for troubleshooting agent behavior.
    Captures detailed information about agent decisions.
    """
    
    def __init__(self):
        self.decisions: List[Dict] = []
        self.tool_calls: List[Dict] = []
        self.errors: List[Dict] = []
        self.enabled = True
    
    def log_decision(self, agent: str, decision: str, reasoning: str = ""):
        """Log an agent decision"""
        if not self.enabled:
            return
        
        self.decisions.append({
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "decision": decision,
            "reasoning": reasoning
        })
    
    def log_tool_call(self, tool: str, inputs: Dict, output: str, success: bool):
        """Log a tool call"""
        if not self.enabled:
            return
        
        self.tool_calls.append({
            "timestamp": datetime.now().isoformat(),
            "tool": tool,
            "inputs": inputs,
            "output": output[:500] if output else "",
            "success": success
        })
    
    def log_error(self, error: str, context: Dict = None):
        """Log an error"""
        self.errors.append({
            "timestamp": datetime.now().isoformat(),
            "error": error,
            "context": context or {}
        })
    
    def get_debug_report(self) -> str:
        """Generate debug report"""
        lines = ["🔍 Debug Report", "=" * 50]
        
        lines.append(f"\n📊 Summary:")
        lines.append(f"  Decisions: {len(self.decisions)}")
        lines.append(f"  Tool calls: {len(self.tool_calls)}")
        lines.append(f"  Errors: {len(self.errors)}")
        
        if self.decisions:
            lines.append(f"\n🧠 Recent Decisions:")
            for d in self.decisions[-5:]:
                lines.append(f"  [{d['agent']}] {d['decision'][:80]}")
        
        if self.tool_calls:
            lines.append(f"\n🔧 Recent Tool Calls:")
            for t in self.tool_calls[-5:]:
                status = "✅" if t['success'] else "❌"
                lines.append(f"  {status} {t['tool']}")
        
        if self.errors:
            lines.append(f"\n❌ Recent Errors:")
            for e in self.errors[-5:]:
                lines.append(f"  {e['error'][:80]}")
        
        return "\n".join(lines)
    
    def clear(self):
        """Clear debug context"""
        self.decisions.clear()
        self.tool_calls.clear()
        self.errors.clear()


# Global debug context
_debug_context = DebugContext()


def get_debug_context() -> DebugContext:
    """Get global debug context"""
    return _debug_context
