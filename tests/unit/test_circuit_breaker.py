"""
Unit tests for Circuit Breaker
"""

import pytest
import asyncio
from orchestrator.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitBreakerManager,
    CircuitState
)


class TestCircuitBreaker:
    """Test cases for CircuitBreaker"""
    
    @pytest.fixture
    def circuit_breaker(self):
        """Create a circuit breaker instance"""
        return CircuitBreaker(
            failure_threshold=3,
            timeout=1.0,
            name="test_circuit"
        )
    
    def test_initial_state(self, circuit_breaker):
        """Test initial circuit breaker state"""
        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker.failure_count == 0
    
    def test_record_success(self, circuit_breaker):
        """Test recording success"""
        circuit_breaker.record_success()
        
        assert circuit_breaker.failure_count == 0
        assert circuit_breaker.state == CircuitState.CLOSED
    
    def test_record_failure(self, circuit_breaker):
        """Test recording failure"""
        circuit_breaker.record_failure()
        
        assert circuit_breaker.failure_count == 1
        assert circuit_breaker.state == CircuitState.CLOSED
    
    def test_circuit_opens_on_threshold(self, circuit_breaker):
        """Test circuit opens when failure threshold is reached"""
        # Record failures up to threshold
        for _ in range(3):
            circuit_breaker.record_failure()
        
        assert circuit_breaker.state == CircuitState.OPEN
        assert circuit_breaker.failure_count == 3
    
    def test_call_success(self, circuit_breaker):
        """Test successful call"""
        def success_func():
            return "success"
        
        result = circuit_breaker.call(success_func)
        
        assert result == "success"
        assert circuit_breaker.state == CircuitState.CLOSED
    
    def test_call_failure(self, circuit_breaker):
        """Test failed call"""
        def failing_func():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError, match="Test error"):
            circuit_breaker.call(failing_func)
        
        assert circuit_breaker.failure_count == 1
    
    def test_call_when_open(self, circuit_breaker):
        """Test call when circuit is open"""
        # Open the circuit
        for _ in range(3):
            circuit_breaker.record_failure()
        
        def any_func():
            return "result"
        
        with pytest.raises(CircuitBreakerOpenError):
            circuit_breaker.call(any_func)
    
    def test_call_async_function_error(self, circuit_breaker):
        """Test that async functions raise error in sync call"""
        async def async_func():
            return "result"
        
        with pytest.raises(ValueError, match="Async function"):
            circuit_breaker.call(async_func)
    
    @pytest.mark.asyncio
    async def test_call_async_success(self, circuit_breaker):
        """Test successful async call"""
        async def async_success():
            return "async_success"
        
        result = await circuit_breaker.call_async(async_success)
        
        assert result == "async_success"
        assert circuit_breaker.state == CircuitState.CLOSED
    
    @pytest.mark.asyncio
    async def test_half_open_state(self, circuit_breaker):
        """Test half-open state transition"""
        # Open the circuit
        for _ in range(3):
            circuit_breaker.record_failure()
        
        assert circuit_breaker.state == CircuitState.OPEN
        
        # Wait for timeout
        await asyncio.sleep(1.1)
        
        # Try to transition to half-open
        circuit_breaker._try_half_open()
        
        # Should be in half-open state
        assert circuit_breaker.state == CircuitState.HALF_OPEN
    
    def test_reset(self, circuit_breaker):
        """Test circuit breaker reset"""
        # Open the circuit
        for _ in range(3):
            circuit_breaker.record_failure()
        
        assert circuit_breaker.state == CircuitState.OPEN
        
        # Reset
        circuit_breaker.reset()
        
        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker.failure_count == 0


class TestCircuitBreakerManager:
    """Test cases for CircuitBreakerManager"""
    
    def test_get_or_create(self):
        """Test getting or creating circuit breaker"""
        manager = CircuitBreakerManager()
        
        cb1 = manager.get_or_create("test_circuit")
        cb2 = manager.get_or_create("test_circuit")
        
        assert cb1 == cb2  # Should return same instance
    
    def test_get_nonexistent(self):
        """Test getting nonexistent circuit breaker"""
        manager = CircuitBreakerManager()
        
        cb = manager.get("nonexistent")
        
        assert cb is None
    
    def test_reset(self):
        """Test resetting circuit breaker"""
        manager = CircuitBreakerManager()
        
        cb = manager.get_or_create("test_circuit", failure_threshold=2)
        
        # Open the circuit
        for _ in range(2):
            cb.record_failure()
        
        assert cb.state == CircuitState.OPEN
        
        # Reset
        manager.reset("test_circuit")
        
        assert cb.state == CircuitState.CLOSED

