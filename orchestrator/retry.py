"""
Retry Mechanisms
Exponential backoff and retry policies for resilient execution
"""

import asyncio
import random
from typing import Dict, Any, Optional, Callable, Type, Tuple
from datetime import datetime
from enum import Enum
from monitoring import get_logger

logger = get_logger(__name__)


class RetryStrategy(str, Enum):
    """Retry strategy types"""
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIXED = "fixed"
    RANDOM = "random"


class RetryPolicy:
    """Retry policy configuration"""
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_multiplier: float = 2.0,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
        retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
        retryable_errors: Optional[list[str]] = None,
        jitter: bool = True
    ):
        """
        Initialize retry policy
        
        Args:
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            backoff_multiplier: Multiplier for exponential backoff
            strategy: Retry strategy (exponential, linear, fixed, random)
            retryable_exceptions: Tuple of exception types that are retryable
            retryable_errors: List of error message patterns that are retryable
            jitter: Whether to add random jitter to delays
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_multiplier = backoff_multiplier
        self.strategy = strategy
        self.retryable_exceptions = retryable_exceptions or (Exception,)
        self.retryable_errors = retryable_errors or []
        self.jitter = jitter
    
    def should_retry(self, attempt: int, exception: Exception) -> bool:
        """
        Check if should retry based on attempt and exception
        
        Args:
            attempt: Current attempt number (0-indexed)
            exception: Exception that occurred
            
        Returns:
            True if should retry
        """
        if attempt >= self.max_retries:
            return False
        
        # Check exception type
        if not isinstance(exception, self.retryable_exceptions):
            return False
        
        # Check error message patterns
        error_message = str(exception).lower()
        if self.retryable_errors:
            if not any(pattern.lower() in error_message for pattern in self.retryable_errors):
                return False
        
        return True
    
    def get_delay(self, attempt: int) -> float:
        """
        Calculate delay for retry attempt
        
        Args:
            attempt: Current attempt number (0-indexed)
            
        Returns:
            Delay in seconds
        """
        if self.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.initial_delay * (self.backoff_multiplier ** attempt)
        elif self.strategy == RetryStrategy.LINEAR:
            delay = self.initial_delay * (attempt + 1)
        elif self.strategy == RetryStrategy.FIXED:
            delay = self.initial_delay
        elif self.strategy == RetryStrategy.RANDOM:
            delay = random.uniform(self.initial_delay, self.max_delay)
        else:
            delay = self.initial_delay
        
        # Apply max delay limit
        delay = min(delay, self.max_delay)
        
        # Add jitter if enabled
        if self.jitter:
            jitter_amount = delay * 0.1  # 10% jitter
            delay = delay + random.uniform(-jitter_amount, jitter_amount)
            delay = max(0, delay)  # Ensure non-negative
        
        return delay


class RetryHandler:
    """Handler for retry operations"""
    
    def __init__(self, policy: Optional[RetryPolicy] = None):
        """
        Initialize retry handler
        
        Args:
            policy: RetryPolicy instance (uses default if not provided)
        """
        self.policy = policy or RetryPolicy()
        logger.info("RetryHandler initialized", policy=self.policy.__dict__)
    
    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute function with retry logic
        
        Args:
            func: Async function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function
            
        Returns:
            Function result
            
        Raises:
            Last exception if all retries fail
        """
        last_exception = None
        
        for attempt in range(self.policy.max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                if attempt > 0:
                    logger.info(
                        "Operation succeeded after retry",
                        attempt=attempt + 1,
                        total_attempts=self.policy.max_retries + 1
                    )
                
                return result
                
            except Exception as e:
                last_exception = e
                
                # Check if should retry
                if not self.policy.should_retry(attempt, e):
                    logger.warning(
                        "Retry not allowed",
                        attempt=attempt + 1,
                        exception_type=type(e).__name__,
                        error=str(e)
                    )
                    raise
                
                # Calculate delay
                delay = self.policy.get_delay(attempt)
                
                logger.warning(
                    "Operation failed, retrying",
                    attempt=attempt + 1,
                    max_attempts=self.policy.max_retries + 1,
                    delay=delay,
                    exception_type=type(e).__name__,
                    error=str(e)
                )
                
                # Wait before retry
                await asyncio.sleep(delay)
        
        # All retries exhausted
        logger.error(
            "All retries exhausted",
            max_attempts=self.policy.max_retries + 1,
            exception_type=type(last_exception).__name__ if last_exception else None,
            error=str(last_exception) if last_exception else None
        )
        
        if last_exception:
            raise last_exception
        
        raise RuntimeError("Retry failed without exception")


def create_retry_policy(config: Dict[str, Any]) -> RetryPolicy:
    """
    Create retry policy from configuration dictionary
    
    Args:
        config: Configuration dictionary
        
    Returns:
        RetryPolicy instance
    """
    return RetryPolicy(
        max_retries=config.get('max_retries', 3),
        initial_delay=config.get('initial_delay', 1.0),
        max_delay=config.get('max_delay', 60.0),
        backoff_multiplier=config.get('backoff_multiplier', 2.0),
        strategy=RetryStrategy(config.get('strategy', 'exponential')),
        retryable_exceptions=tuple(config.get('retryable_exceptions', [Exception])),
        retryable_errors=config.get('retryable_errors', []),
        jitter=config.get('jitter', True)
    )

