"""
Unit tests for Retry mechanism
"""

import pytest
import asyncio
from orchestrator.retry import RetryHandler, RetryPolicy, RetryStrategy


class TestRetryPolicy:
    """Test cases for RetryPolicy"""
    
    def test_policy_initialization(self):
        """Test retry policy initialization"""
        policy = RetryPolicy(
            max_retries=3,
            initial_delay=1.0,
            strategy=RetryStrategy.EXPONENTIAL
        )
        
        assert policy.max_retries == 3
        assert policy.initial_delay == 1.0
        assert policy.strategy == RetryStrategy.EXPONENTIAL
    
    def test_should_retry(self):
        """Test should_retry logic"""
        policy = RetryPolicy(max_retries=3)
        
        # Should retry if attempt < max_retries
        assert policy.should_retry(0, Exception("test")) is True
        assert policy.should_retry(1, Exception("test")) is True
        assert policy.should_retry(2, Exception("test")) is True
        assert policy.should_retry(3, Exception("test")) is False
    
    def test_get_delay_exponential(self):
        """Test exponential delay calculation"""
        policy = RetryPolicy(
            initial_delay=1.0,
            max_delay=60.0,
            strategy=RetryStrategy.EXPONENTIAL,
            backoff_multiplier=2.0,
            jitter=False  # Disable jitter for predictable tests
        )
        
        delay1 = policy.get_delay(0)
        delay2 = policy.get_delay(1)
        delay3 = policy.get_delay(2)
        
        assert delay1 == 1.0
        assert delay2 == 2.0
        assert delay3 == 4.0
        assert delay3 <= 60.0
    
    def test_get_delay_linear(self):
        """Test linear delay calculation"""
        policy = RetryPolicy(
            initial_delay=1.0,
            strategy=RetryStrategy.LINEAR,
            jitter=False  # Disable jitter for predictable tests
        )
        
        delay1 = policy.get_delay(0)
        delay2 = policy.get_delay(1)
        delay3 = policy.get_delay(2)
        
        assert delay1 == 1.0
        assert delay2 == 2.0
        assert delay3 == 3.0
    
    def test_get_delay_fixed(self):
        """Test fixed delay calculation"""
        policy = RetryPolicy(
            initial_delay=2.0,
            strategy=RetryStrategy.FIXED,
            jitter=False  # Disable jitter for predictable tests
        )
        
        delay1 = policy.get_delay(0)
        delay2 = policy.get_delay(1)
        delay3 = policy.get_delay(2)
        
        assert delay1 == 2.0
        assert delay2 == 2.0
        assert delay3 == 2.0


class TestRetryHandler:
    """Test cases for RetryHandler"""
    
    @pytest.mark.asyncio
    async def test_successful_execution(self):
        """Test successful execution without retry"""
        handler = RetryHandler(RetryPolicy(max_retries=3))
        
        async def success_func():
            return "success"
        
        result = await handler.execute_with_retry(success_func)
        
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_retry_on_failure(self):
        """Test retry on failure"""
        attempts = []
        
        async def failing_func():
            attempts.append(1)
            if len(attempts) < 3:
                raise Exception("Temporary failure")
            return "success"
        
        policy = RetryPolicy(
            max_retries=3,
            initial_delay=0.1,  # Short delay for testing
            strategy=RetryStrategy.FIXED
        )
        handler = RetryHandler(policy)
        
        result = await handler.execute_with_retry(failing_func)
        
        assert result == "success"
        assert len(attempts) == 3
    
    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """Test when max retries are exceeded"""
        attempts = []
        
        async def always_failing_func():
            attempts.append(1)
            raise Exception("Always fails")
        
        policy = RetryPolicy(
            max_retries=2,
            initial_delay=0.1,
            strategy=RetryStrategy.FIXED
        )
        handler = RetryHandler(policy)
        
        with pytest.raises(Exception, match="Always fails"):
            await handler.execute_with_retry(always_failing_func)
        
        assert len(attempts) == 3  # Initial + 2 retries
    
    @pytest.mark.asyncio
    async def test_sync_function(self):
        """Test retry with synchronous function"""
        handler = RetryHandler(RetryPolicy(max_retries=2))
        
        def sync_success_func():
            return "sync_success"
        
        result = await handler.execute_with_retry(sync_success_func)
        
        assert result == "sync_success"

