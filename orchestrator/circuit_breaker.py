"""
Circuit Breaker Pattern
Prevents cascade failures by breaking circuit when failure threshold is reached
"""

from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
from monitoring import get_logger

logger = get_logger(__name__)


class CircuitState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, failing fast
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker implementation
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Circuit is open, requests fail immediately
    - HALF_OPEN: Testing recovery, limited requests allowed
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        half_open_max_calls: int = 3,
        success_threshold: int = 2,
        name: Optional[str] = None
    ):
        """
        Initialize circuit breaker
        
        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Time in seconds before trying half-open state
            half_open_max_calls: Max calls allowed in half-open state
            success_threshold: Number of successes needed to close circuit
            name: Optional name for the circuit breaker
        """
        self.name = name or "default"
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.half_open_max_calls = half_open_max_calls
        self.success_threshold = success_threshold
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.half_open_calls = 0
        
        logger.info(
            "CircuitBreaker initialized",
            name=self.name,
            failure_threshold=failure_threshold,
            timeout=timeout
        )
    
    def record_success(self):
        """Record a successful call"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            
            logger.debug(
                "Success recorded in half-open state",
                name=self.name,
                success_count=self.success_count,
                threshold=self.success_threshold
            )
            
            # Close circuit if enough successes
            if self.success_count >= self.success_threshold:
                self._close_circuit()
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0
    
    def record_failure(self):
        """Record a failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        logger.warning(
            "Failure recorded",
            name=self.name,
            failure_count=self.failure_count,
            threshold=self.failure_threshold,
            state=self.state
        )
        
        # Open circuit if threshold reached
        if self.state == CircuitState.CLOSED and self.failure_count >= self.failure_threshold:
            self._open_circuit()
        elif self.state == CircuitState.HALF_OPEN:
            # Any failure in half-open state opens circuit again
            self._open_circuit()
    
    def _open_circuit(self):
        """Open the circuit"""
        old_state = self.state
        self.state = CircuitState.OPEN
        self.half_open_calls = 0
        self.success_count = 0
        
        logger.warning(
            "Circuit opened",
            name=self.name,
            old_state=old_state,
            failure_count=self.failure_count
        )
    
    def _close_circuit(self):
        """Close the circuit"""
        old_state = self.state
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0
        
        logger.info(
            "Circuit closed",
            name=self.name,
            old_state=old_state
        )
    
    def _try_half_open(self):
        """Try to transition to half-open state"""
        if self.state == CircuitState.OPEN:
            if self.last_failure_time:
                elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
                if elapsed >= self.timeout:
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_calls = 0
                    self.success_count = 0
                    
                    logger.info(
                        "Circuit transitioned to half-open",
                        name=self.name,
                        elapsed=elapsed
                    )
                    return True
        return False
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError if circuit is open
            Original exception if call fails
        """
        import asyncio
        
        # Try to transition to half-open if needed
        self._try_half_open()
        
        # Check circuit state
        if self.state == CircuitState.OPEN:
            raise CircuitBreakerOpenError(
                f"Circuit breaker '{self.name}' is OPEN",
                self.name
            )
        
        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_calls >= self.half_open_max_calls:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is HALF_OPEN (max calls reached)",
                    self.name
                )
            self.half_open_calls += 1
        
        # Execute function
        try:
            if asyncio.iscoroutinefunction(func):
                # For async functions, we need to use async context
                # This is a sync wrapper, so we'll handle it differently
                result = func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            self.record_success()
            return result
            
        except Exception as e:
            self.record_failure()
            raise
    
    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute async function with circuit breaker protection
        
        Args:
            func: Async function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError if circuit is open
            Original exception if call fails
        """
        # Try to transition to half-open if needed
        self._try_half_open()
        
        # Check circuit state
        if self.state == CircuitState.OPEN:
            raise CircuitBreakerOpenError(
                f"Circuit breaker '{self.name}' is OPEN",
                self.name
            )
        
        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_calls >= self.half_open_max_calls:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is HALF_OPEN (max calls reached)",
                    self.name
                )
            self.half_open_calls += 1
        
        # Execute function
        try:
            result = await func(*args, **kwargs)
            self.record_success()
            return result
            
        except CircuitBreakerOpenError:
            raise
        except Exception as e:
            self.record_failure()
            raise
    
    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state"""
        return {
            'name': self.name,
            'state': self.state,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'half_open_calls': self.half_open_calls,
            'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None,
            'failure_threshold': self.failure_threshold,
            'timeout': self.timeout
        }
    
    def reset(self):
        """Reset circuit breaker to closed state"""
        self._close_circuit()
        logger.info("Circuit breaker reset", name=self.name)


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open"""
    
    def __init__(self, message: str, circuit_name: str):
        super().__init__(message)
        self.circuit_name = circuit_name


class CircuitBreakerManager:
    """Manager for multiple circuit breakers"""
    
    def __init__(self):
        """Initialize circuit breaker manager"""
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        logger.info("CircuitBreakerManager initialized")
    
    def get_or_create(
        self,
        name: str,
        **kwargs
    ) -> CircuitBreaker:
        """
        Get existing circuit breaker or create new one
        
        Args:
            name: Circuit breaker name
            **kwargs: Circuit breaker configuration
            
        Returns:
            CircuitBreaker instance
        """
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(name=name, **kwargs)
        
        return self.circuit_breakers[name]
    
    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name"""
        return self.circuit_breakers.get(name)
    
    def reset(self, name: Optional[str] = None):
        """Reset circuit breaker(s)"""
        if name:
            if name in self.circuit_breakers:
                self.circuit_breakers[name].reset()
        else:
            for cb in self.circuit_breakers.values():
                cb.reset()

