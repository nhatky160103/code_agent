"""Rate limiting and retry utilities for Code Agent"""
import time
import random
from typing import Callable, Any, Optional
from functools import wraps

try:
    from tenacity import (
        retry,
        stop_after_attempt,
        wait_exponential,
        wait_fixed,
        retry_if_exception_type,
        retry_if_result,
        RetryError
    )
    TENACITY_AVAILABLE = True
except ImportError:
    TENACITY_AVAILABLE = False

try:
    from circuitbreaker import circuit
    CIRCUIT_BREAKER_AVAILABLE = True
except ImportError:
    CIRCUIT_BREAKER_AVAILABLE = False
    circuit = lambda **kwargs: lambda f: f  # Dummy decorator


class RateLimiter:
    """Simple rate limiter using token bucket algorithm"""
    
    def __init__(self, max_calls: int = 60, period: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_calls: Maximum number of calls allowed
            period: Time period in seconds
        """
        self.max_calls = max_calls
        self.period = period
        self.calls = []
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator to rate limit a function"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            
            # Remove old calls outside the period
            self.calls = [call_time for call_time in self.calls if now - call_time < self.period]
            
            # Check if we've exceeded the limit
            if len(self.calls) >= self.max_calls:
                # Calculate wait time
                oldest_call = min(self.calls)
                wait_time = self.period - (now - oldest_call) + 0.1
                if wait_time > 0:
                    time.sleep(wait_time)
                    # Clean up again after waiting
                    now = time.time()
                    self.calls = [call_time for call_time in self.calls if now - call_time < self.period]
            
            # Record this call
            self.calls.append(time.time())
            
            # Execute function
            return func(*args, **kwargs)
        
        return wrapper


def _is_rate_limit_error(exception: Exception) -> bool:
    """Check if exception is a rate limit error"""
    error_str = str(exception).lower()
    return any(keyword in error_str for keyword in [
        "rate limit",
        "rate_limit",
        "429",
        "quota exceeded",
        "too many requests",
        "throttle"
    ])


def _is_api_error(exception: Exception) -> bool:
    """Check if exception is an API error that should be retried"""
    error_str = str(exception).lower()
    # Retry on network errors, timeouts, and 5xx errors
    return any(keyword in error_str for keyword in [
        "timeout",
        "connection",
        "network",
        "500",
        "502",
        "503",
        "504"
    ])


def call_llm_with_retry(
    max_retries: int = 3,
    initial_wait: float = 1.0,
    max_wait: float = 60.0,
    exponential_base: float = 2.0,
    enable_circuit_breaker: bool = True
):
    """
    Decorator to retry LLM calls with exponential backoff and circuit breaker.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_wait: Initial wait time in seconds
        max_wait: Maximum wait time in seconds
        exponential_base: Base for exponential backoff
        enable_circuit_breaker: Enable circuit breaker pattern
        
    Usage:
        @call_llm_with_retry(max_retries=5, initial_wait=2.0)
        def call_llm(messages, model):
            ...
    """
    def decorator(func: Callable) -> Callable:
        # Apply circuit breaker if available
        if enable_circuit_breaker and CIRCUIT_BREAKER_AVAILABLE:
            func = circuit(
                failure_threshold=5,
                recovery_timeout=60,
                expected_exception=Exception
            )(func)
        
        # Apply retry logic if tenacity is available
        if TENACITY_AVAILABLE:
            @retry(
                stop=stop_after_attempt(max_retries + 1),
                wait=wait_exponential(
                    multiplier=initial_wait,
                    min=initial_wait,
                    max=max_wait,
                    exp_base=exponential_base
                ),
                retry=retry_if_exception_type(Exception) & (
                    retry_if_result(lambda x: False) |  # Never retry on result
                    retry_if_exception_type(Exception)  # Retry on exceptions
                ),
                reraise=True
            )
            @wraps(func)
            def wrapper_with_retry(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # Add jitter to avoid thundering herd
                    if _is_rate_limit_error(e):
                        jitter = random.uniform(0, 5)
                        time.sleep(jitter)
                    raise
        
            return wrapper_with_retry
        else:
            # Fallback: manual retry logic
            @wraps(func)
            def wrapper_manual(*args, **kwargs):
                last_exception = None
                
                for attempt in range(max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        
                        # Don't retry on last attempt
                        if attempt == max_retries:
                            break
                        
                        # Calculate wait time with exponential backoff
                        wait_time = min(
                            initial_wait * (exponential_base ** attempt),
                            max_wait
                        )
                        
                        # Add jitter
                        jitter = random.uniform(0, wait_time * 0.1)
                        wait_time += jitter
                        
                        # Special handling for rate limit errors
                        if _is_rate_limit_error(e):
                            wait_time = max(wait_time, 15)  # Minimum 15s for rate limits
                        
                        time.sleep(wait_time)
                
                # Re-raise last exception
                raise last_exception
            
            return wrapper_manual
    
    return decorator


def retry_on_failure(
    max_retries: int = 3,
    wait_time: float = 1.0,
    exceptions: tuple = (Exception,)
):
    """
    Simple retry decorator for any function.
    
    Args:
        max_retries: Maximum number of retries
        wait_time: Wait time between retries in seconds
        exceptions: Tuple of exceptions to catch and retry
        
    Usage:
        @retry_on_failure(max_retries=5, wait_time=2.0)
        def unreliable_function():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        time.sleep(wait_time * (attempt + 1))  # Linear backoff
                    else:
                        raise
            
            if last_exception:
                raise last_exception
        
        return wrapper
    
    return decorator

