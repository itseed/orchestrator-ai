"""
Distributed Tracing
Correlation IDs and distributed tracing support
"""

import uuid
from typing import Dict, Any, Optional, ContextManager
from contextlib import contextmanager
from datetime import datetime
import structlog.contextvars
from monitoring import get_logger

logger = get_logger(__name__)


class TraceContext:
    """Trace context for distributed tracing"""
    
    def __init__(
        self,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ):
        """
        Initialize trace context
        
        Args:
            trace_id: Unique trace ID (auto-generated if not provided)
            span_id: Current span ID (auto-generated if not provided)
            parent_span_id: Parent span ID for nested spans
            correlation_id: Correlation ID for request tracking
        """
        self.trace_id = trace_id or str(uuid.uuid4())
        self.span_id = span_id or str(uuid.uuid4())
        self.parent_span_id = parent_span_id
        self.correlation_id = correlation_id or self.trace_id
        self.start_time = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert trace context to dictionary"""
        return {
            'trace_id': self.trace_id,
            'span_id': self.span_id,
            'parent_span_id': self.parent_span_id,
            'correlation_id': self.correlation_id,
            'start_time': self.start_time.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TraceContext":
        """Create trace context from dictionary"""
        return cls(
            trace_id=data.get('trace_id'),
            span_id=data.get('span_id'),
            parent_span_id=data.get('parent_span_id'),
            correlation_id=data.get('correlation_id')
        )
    
    def create_child_span(self) -> "TraceContext":
        """Create child span context"""
        return TraceContext(
            trace_id=self.trace_id,
            parent_span_id=self.span_id,
            correlation_id=self.correlation_id
        )


class Tracer:
    """Distributed tracer"""
    
    def __init__(self):
        """Initialize tracer"""
        self._current_context: Optional[TraceContext] = None
        logger.info("Tracer initialized")
    
    def start_trace(
        self,
        correlation_id: Optional[str] = None,
        trace_id: Optional[str] = None
    ) -> TraceContext:
        """
        Start a new trace
        
        Args:
            correlation_id: Optional correlation ID
            trace_id: Optional trace ID
            
        Returns:
            TraceContext instance
        """
        context = TraceContext(
            trace_id=trace_id,
            correlation_id=correlation_id
        )
        self._current_context = context
        
        # Bind to structlog context
        structlog.contextvars.bind_contextvars(
            trace_id=context.trace_id,
            span_id=context.span_id,
            correlation_id=context.correlation_id
        )
        
        logger.info(
            "Trace started",
            trace_id=context.trace_id,
            correlation_id=context.correlation_id
        )
        
        return context
    
    def get_current_context(self) -> Optional[TraceContext]:
        """Get current trace context"""
        return self._current_context
    
    def set_context(self, context: TraceContext):
        """Set current trace context"""
        self._current_context = context
        
        # Bind to structlog context
        structlog.contextvars.bind_contextvars(
            trace_id=context.trace_id,
            span_id=context.span_id,
            correlation_id=context.correlation_id
        )
    
    @contextmanager
    def span(
        self,
        operation_name: str,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """
        Create a span context manager
        
        Args:
            operation_name: Name of the operation
            attributes: Optional span attributes
        """
        parent_context = self._current_context
        
        if parent_context:
            child_context = parent_context.create_child_span()
        else:
            child_context = TraceContext()
        
        self.set_context(child_context)
        
        # Add operation name to context
        structlog.contextvars.bind_contextvars(
            operation=operation_name,
            **(attributes or {})
        )
        
        start_time = datetime.utcnow()
        
        try:
            logger.info(
                "Span started",
                operation=operation_name,
                span_id=child_context.span_id,
                parent_span_id=child_context.parent_span_id
            )
            
            yield child_context
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.error(
                "Span failed",
                operation=operation_name,
                span_id=child_context.span_id,
                duration=duration,
                error=str(e),
                exc_info=True
            )
            raise
        finally:
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info(
                "Span completed",
                operation=operation_name,
                span_id=child_context.span_id,
                duration=duration
            )
            
            # Restore parent context
            if parent_context:
                self.set_context(parent_context)
            else:
                self._current_context = None
                structlog.contextvars.clear_contextvars()
    
    def clear_context(self):
        """Clear current trace context"""
        self._current_context = None
        structlog.contextvars.clear_contextvars()


# Global tracer instance
_tracer: Optional[Tracer] = None


def get_tracer() -> Tracer:
    """Get global tracer instance"""
    global _tracer
    if _tracer is None:
        _tracer = Tracer()
    return _tracer


def get_correlation_id() -> Optional[str]:
    """Get current correlation ID from trace context"""
    tracer = get_tracer()
    context = tracer.get_current_context()
    return context.correlation_id if context else None


def set_correlation_id(correlation_id: str):
    """Set correlation ID"""
    tracer = get_tracer()
    context = tracer.get_current_context()
    
    if context:
        context.correlation_id = correlation_id
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)
    else:
        # Create new trace with correlation ID
        tracer.start_trace(correlation_id=correlation_id)

