"""
AtomAgent Retry Mechanism
Exponential backoff and smart retry strategies
"""
import time
import random
from typing import Callable, Any, Optional, Type, Tuple
from functools import wraps

from utils.logger import get_logger

logger = get_logger()

# Try to import tenacity, fallback to simple implementation
try:
    from tenacity import (
        retry,
        stop_after_attempt,
        wait_exponential,
        retry_if_exception_type,
        before_sleep_log,
        RetryError
    )
    TENACITY_AVAILABLE = True
except ImportError:
    TENACITY_AVAILABLE = False
    logger.warning("tenacity not installed, using simple retry")


def is_retryable_error(error: Exception) -> bool:
    """Check if error is retryable"""
    error_str = str(error).lower()
    
    retryable_patterns = [
        "rate limit", "429", "too many requests",
        "timeout", "timed out",
        "connection", "network",
        "502", "503", "504",
        "temporary", "overloaded",
        "service unavailable"
    ]
    
    return any(pattern in error_str for pattern in retryable_patterns)


def is_permanent_error(error: Exception) -> bool:
    """Check if error is permanent (should not retry)"""
    error_str = str(error).lower()
    
    permanent_patterns = [
        "invalid api key", "authentication",
        "unauthorized", "403", "401",
        "invalid model", "model not found",
        "invalid request", "bad request"
    ]
    
    return any(pattern in error_str for pattern in permanent_patterns)


class SimpleRetry:
    """Simple retry implementation without tenacity"""
    
    def __init__(self, max_attempts: int = 3, 
                 base_delay: float = 1.0,
                 max_delay: float = 60.0,
                 exponential_base: float = 2.0,
                 jitter: bool = True):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff"""
        delay = self.base_delay * (self.exponential_base ** attempt)
        delay = min(delay, self.max_delay)
        
        if self.jitter:
            delay = delay * (0.5 + random.random())
        
        return delay
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            
            for attempt in range(self.max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    
                    # Don't retry permanent errors
                    if is_permanent_error(e):
                        logger.error(f"Permanent error, not retrying: {e}")
                        raise
                    
                    # Check if retryable
                    if not is_retryable_error(e) and attempt > 0:
                        logger.warning(f"Non-retryable error: {e}")
                        raise
                    
                    if attempt < self.max_attempts - 1:
                        delay = self.calculate_delay(attempt)
                        logger.warning(
                            f"Attempt {attempt + 1}/{self.max_attempts} failed: {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        time.sleep(delay)
            
            raise last_error
        
        return wrapper


def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorator for retry with exponential backoff.
    Uses tenacity if available, otherwise falls back to simple implementation.
    
    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Initial delay between retries (seconds)
        max_delay: Maximum delay between retries (seconds)
        retryable_exceptions: Tuple of exception types to retry
    
    Usage:
        @retry_with_backoff(max_attempts=3)
        def my_function():
            ...
    """
    if TENACITY_AVAILABLE:
        return retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=base_delay, max=max_delay),
            retry=retry_if_exception_type(retryable_exceptions),
            before_sleep=before_sleep_log(logger.logger, log_level=30)  # WARNING
        )
    else:
        return SimpleRetry(
            max_attempts=max_attempts,
            base_delay=base_delay,
            max_delay=max_delay
        )


def retry_on_rate_limit(func: Callable) -> Callable:
    """
    Decorator specifically for rate limit handling.
    Includes API key rotation support.
    
    Usage:
        @retry_on_rate_limit
        def call_api():
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        max_attempts = 5
        last_error = None
        
        for attempt in range(max_attempts):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                
                # Check if rate limit
                if "rate limit" in error_str or "429" in error_str:
                    # Try to rotate API key
                    try:
                        from core.providers import handle_rate_limit
                        # Extract provider from function if possible
                        provider = getattr(func, '_provider', None)
                        if provider and handle_rate_limit(provider):
                            logger.info(f"Rotated API key for {provider}")
                            continue
                    except:
                        pass
                    
                    # Exponential backoff
                    delay = min(2 ** attempt * 2, 60)
                    logger.warning(f"Rate limit hit, waiting {delay}s...")
                    time.sleep(delay)
                    continue
                
                # Not a rate limit error
                raise
        
        raise last_error
    
    return wrapper


class RetryContext:
    """
    Context manager for retry operations with state tracking.
    
    Usage:
        with RetryContext(max_attempts=3) as ctx:
            while ctx.should_retry():
                try:
                    result = do_something()
                    ctx.success()
                    break
                except Exception as e:
                    ctx.failed(e)
    """
    
    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.attempt = 0
        self.last_error: Optional[Exception] = None
        self._success = False
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def should_retry(self) -> bool:
        """Check if should continue retrying"""
        if self._success:
            return False
        return self.attempt < self.max_attempts
    
    def failed(self, error: Exception):
        """Record a failed attempt"""
        self.last_error = error
        self.attempt += 1
        
        if self.attempt < self.max_attempts:
            delay = self.base_delay * (2 ** (self.attempt - 1))
            delay = min(delay, 30)
            logger.warning(
                f"Attempt {self.attempt}/{self.max_attempts} failed: {error}. "
                f"Retrying in {delay:.1f}s..."
            )
            time.sleep(delay)
    
    def success(self):
        """Mark operation as successful"""
        self._success = True
    
    def raise_if_failed(self):
        """Raise last error if all attempts failed"""
        if not self._success and self.last_error:
            raise self.last_error
