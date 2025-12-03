"""
AtomAgent Utilities
"""
from utils.logger import get_logger, log_execution

__all__ = [
    "get_logger",
    "log_execution",
]

# Lazy imports for optional modules
def get_cache():
    from utils.cache import get_cache as _get_cache
    return _get_cache()

def get_tracer():
    from utils.telemetry import get_tracer as _get_tracer
    return _get_tracer()

def get_context_manager(model: str = "default"):
    from utils.context_manager import get_context_manager as _get_context_manager
    return _get_context_manager(model)
