"""
Intelligent Rate Limiter with Adaptive Backoff Strategy
Handles API rate limits professionally with context-aware retry logic
"""

import time
import asyncio
from typing import Callable, Any, Optional, Dict, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)


class Priority(Enum):
    """Request priority levels"""
    CRITICAL = 1    # Must complete (e.g., final PR generation)
    HIGH = 2        # Important (e.g., core logic files)
    MEDIUM = 3      # Standard (e.g., regular files)
    LOW = 4         # Can retry later (e.g., documentation)


@dataclass
class RequestMetrics:
    """Track request metrics for intelligent decision making"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rate_limited_requests: int = 0
    consecutive_failures: int = 0
    last_success_time: Optional[datetime] = None
    last_failure_time: Optional[datetime] = None
    average_response_time: float = 0.0
    response_times: List[float] = field(default_factory=list)
    
    def record_success(self, response_time: float):
        """Record successful request"""
        self.total_requests += 1
        self.successful_requests += 1
        self.consecutive_failures = 0
        self.last_success_time = datetime.now()
        self.response_times.append(response_time)
        
        # Keep only last 50 response times for average calculation
        if len(self.response_times) > 50:
            self.response_times = self.response_times[-50:]
        
        self.average_response_time = sum(self.response_times) / len(self.response_times)
    
    def record_failure(self, is_rate_limit: bool = False):
        """Record failed request"""
        self.total_requests += 1
        self.failed_requests += 1
        self.consecutive_failures += 1
        self.last_failure_time = datetime.now()
        
        if is_rate_limit:
            self.rate_limited_requests += 1
    
    def get_success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests
    
    def should_use_circuit_breaker(self) -> bool:
        """Determine if circuit breaker should activate"""
        # Activate if 5+ consecutive failures or success rate < 30%
        return (self.consecutive_failures >= 5 or 
                (self.total_requests > 10 and self.get_success_rate() < 0.3))


class AdaptiveRateLimiter:
    """
    Intelligent rate limiter with multiple strategies:
    1. Exponential backoff with jitter
    2. Token bucket algorithm
    3. Adaptive delay based on API response patterns
    4. Priority queue for critical requests
    5. Circuit breaker for sustained failures
    """
    
    def __init__(
        self,
        max_requests_per_minute: int = 15,
        max_concurrent_requests: int = 3,
        base_delay_seconds: float = 5.0,
        max_delay_seconds: float = 120.0,
        circuit_breaker_threshold: int = 5,
        circuit_breaker_timeout: int = 180,
    ):
        self.max_requests_per_minute = max_requests_per_minute
        self.max_concurrent_requests = max_concurrent_requests
        self.base_delay = base_delay_seconds
        self.max_delay = max_delay_seconds
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.circuit_breaker_timeout = circuit_breaker_timeout
        
        # Token bucket for rate limiting
        self.tokens = max_requests_per_minute
        self.last_refill = datetime.now()
        
        # Track active requests
        self.active_requests = 0
        
        # Metrics tracking
        self.metrics = RequestMetrics()
        
        # Circuit breaker state
        self.circuit_open = False
        self.circuit_open_until: Optional[datetime] = None
        
        # Request queue by priority
        self.request_queue: Dict[Priority, List] = {
            Priority.CRITICAL: [],
            Priority.HIGH: [],
            Priority.MEDIUM: [],
            Priority.LOW: []
        }
        
        logger.info(
            "rate_limiter_initialized",
            max_rpm=max_requests_per_minute,
            max_concurrent=max_concurrent_requests,
            base_delay=base_delay_seconds
        )
    
    def _refill_tokens(self):
        """Refill token bucket based on elapsed time"""
        now = datetime.now()
        elapsed = (now - self.last_refill).total_seconds()
        
        # Refill rate: max_requests_per_minute tokens per 60 seconds
        tokens_to_add = (elapsed / 60.0) * self.max_requests_per_minute
        self.tokens = min(self.max_requests_per_minute, self.tokens + tokens_to_add)
        self.last_refill = now
    
    def _calculate_delay(self, attempt: int, priority: Priority) -> float:
        """
        Calculate intelligent delay based on:
        - Attempt number (exponential backoff)
        - Priority (critical requests get shorter delays)
        - Current success rate
        - Recent response times
        """
        # Base exponential backoff: base_delay * (2 ^ attempt)
        exponential_delay = min(
            self.base_delay * (2 ** attempt),
            self.max_delay
        )
        
        # Priority multiplier (critical requests wait less)
        priority_multipliers = {
            Priority.CRITICAL: 0.5,
            Priority.HIGH: 0.75,
            Priority.MEDIUM: 1.0,
            Priority.LOW: 1.5
        }
        delay = exponential_delay * priority_multipliers.get(priority, 1.0)
        
        # Adaptive adjustment based on success rate
        success_rate = self.metrics.get_success_rate()
        if success_rate < 0.5:
            # If success rate is low, increase delays
            delay *= 1.5
        elif success_rate > 0.8:
            # If success rate is high, can be more aggressive
            delay *= 0.8
        
        # Add jitter to prevent thundering herd (±20%)
        import random
        jitter = delay * 0.2 * (random.random() - 0.5) * 2
        delay += jitter
        
        return max(1.0, min(delay, self.max_delay))
    
    def _check_circuit_breaker(self):
        """Check and manage circuit breaker state"""
        now = datetime.now()
        
        # Check if circuit should be closed (timeout expired)
        if self.circuit_open and self.circuit_open_until:
            if now >= self.circuit_open_until:
                logger.info(
                    "circuit_breaker_closing",
                    was_open_for=self.circuit_breaker_timeout
                )
                self.circuit_open = False
                self.circuit_open_until = None
                self.metrics.consecutive_failures = 0
                return
        
        # Check if circuit should open
        if self.metrics.should_use_circuit_breaker():
            if not self.circuit_open:
                self.circuit_open = True
                self.circuit_open_until = now + timedelta(seconds=self.circuit_breaker_timeout)
                logger.warning(
                    "circuit_breaker_opened",
                    consecutive_failures=self.metrics.consecutive_failures,
                    success_rate=self.metrics.get_success_rate(),
                    timeout=self.circuit_breaker_timeout
                )
    
    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        max_retries: int = 5,
        priority: Priority = Priority.MEDIUM,
        context: Optional[str] = None,
        **kwargs
    ) -> Any:
        """
        Execute function with intelligent retry logic
        
        Args:
            func: Async or sync function to execute
            *args: Positional arguments for func
            max_retries: Maximum number of retry attempts
            priority: Request priority level
            context: Description of what this request is for (for logging)
            **kwargs: Keyword arguments for func
        
        Returns:
            Result from successful function execution
        
        Raises:
            Exception: If all retries exhausted or circuit breaker is open
        """
        attempt = 0
        last_exception = None
        
        logger.info(
            "request_queued",
            context=context,
            priority=priority.name,
            max_retries=max_retries
        )
        
        while attempt < max_retries:
            try:
                # Check circuit breaker
                self._check_circuit_breaker()
                if self.circuit_open:
                    wait_time = (self.circuit_open_until - datetime.now()).total_seconds()
                    if wait_time > 0:
                        logger.warning(
                            "circuit_breaker_waiting",
                            context=context,
                            wait_seconds=wait_time
                        )
                        # For critical requests, wait; for others, fail fast
                        if priority in [Priority.CRITICAL, Priority.HIGH]:
                            await asyncio.sleep(wait_time)
                            self._check_circuit_breaker()
                        else:
                            raise RuntimeError(
                                f"Circuit breaker OPEN. System is recovering. "
                                f"Please wait {wait_time:.0f}s and retry. "
                                f"(Consecutive failures: {self.metrics.consecutive_failures})"
                            )
                
                # Token bucket: wait for token availability
                self._refill_tokens()
                if self.tokens < 1:
                    wait_for_token = 60.0 / self.max_requests_per_minute
                    logger.info(
                        "rate_limit_waiting_for_token",
                        context=context,
                        wait_seconds=wait_for_token
                    )
                    await asyncio.sleep(wait_for_token)
                    self._refill_tokens()
                
                # Concurrency limit
                while self.active_requests >= self.max_concurrent_requests:
                    logger.debug(
                        "waiting_for_slot",
                        active=self.active_requests,
                        max_concurrent=self.max_concurrent_requests
                    )
                    await asyncio.sleep(1)
                
                # Consume token and execute
                self.tokens -= 1
                self.active_requests += 1
                
                start_time = time.time()
                
                logger.info(
                    "request_executing",
                    context=context,
                    attempt=attempt + 1,
                    priority=priority.name,
                    tokens_remaining=self.tokens
                )
                
                # Execute function (handle both async and sync)
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # Record success
                response_time = time.time() - start_time
                self.metrics.record_success(response_time)
                self.active_requests -= 1
                
                logger.info(
                    "request_succeeded",
                    context=context,
                    attempt=attempt + 1,
                    response_time=response_time,
                    success_rate=self.metrics.get_success_rate()
                )
                
                return result
                
            except Exception as e:
                self.active_requests = max(0, self.active_requests - 1)
                error_str = str(e).lower()
                is_rate_limit = any(
                    keyword in error_str 
                    for keyword in ['rate limit', 'quota', 'too many requests', '429']
                )
                
                self.metrics.record_failure(is_rate_limit=is_rate_limit)
                last_exception = e
                
                if is_rate_limit:
                    delay = self._calculate_delay(attempt, priority)
                    
                    logger.warning(
                        "rate_limit_hit",
                        context=context,
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        delay=delay,
                        consecutive_failures=self.metrics.consecutive_failures,
                        error=str(e)
                    )
                    
                    # Don't retry if we've exhausted attempts
                    if attempt >= max_retries - 1:
                        logger.error(
                            "request_failed_permanently",
                            context=context,
                            total_attempts=attempt + 1,
                            error=str(e)
                        )
                        raise RuntimeError(
                            f"Rate limit exceeded after {max_retries} attempts for: {context}. "
                            f"Error: {str(e)}"
                        )
                    
                    # Wait with adaptive delay
                    logger.info(
                        "backing_off",
                        context=context,
                        delay_seconds=delay,
                        attempt=attempt + 1
                    )
                    await asyncio.sleep(delay)
                    attempt += 1
                    
                else:
                    # Non rate-limit error, fail immediately
                    logger.error(
                        "request_failed_non_rate_limit",
                        context=context,
                        error=str(e),
                        error_type=type(e).__name__
                    )
                    raise
        
        # All retries exhausted
        raise RuntimeError(
            f"Failed to complete request after {max_retries} attempts: {context}. "
            f"Last error: {str(last_exception)}"
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get current rate limiter status"""
        self._refill_tokens()
        return {
            "tokens_available": self.tokens,
            "active_requests": self.active_requests,
            "circuit_breaker_open": self.circuit_open,
            "metrics": {
                "total_requests": self.metrics.total_requests,
                "successful_requests": self.metrics.successful_requests,
                "failed_requests": self.metrics.failed_requests,
                "rate_limited_requests": self.metrics.rate_limited_requests,
                "success_rate": self.metrics.get_success_rate(),
                "average_response_time": self.metrics.average_response_time,
                "consecutive_failures": self.metrics.consecutive_failures
            }
        }


# Sync wrapper for backwards compatibility
class SyncRateLimiter:
    """Synchronous wrapper around AdaptiveRateLimiter"""
    
    def __init__(self, *args, **kwargs):
        self.async_limiter = AdaptiveRateLimiter(*args, **kwargs)
    
    def execute_with_retry(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute function with retry in sync context"""
        # Create new event loop if needed
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self.async_limiter.execute_with_retry(func, *args, **kwargs)
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get status (sync version)"""
        return self.async_limiter.get_status()
