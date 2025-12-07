"""
Metrics Collection
Prometheus metrics and monitoring
"""

from typing import Dict, Any, Optional
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Summary,
    start_http_server,
    REGISTRY
)
from monitoring import get_logger

logger = get_logger(__name__)


class MetricsCollector:
    """
    Metrics collector for orchestrator system
    
    Tracks:
    - Task execution metrics
    - Agent performance metrics
    - Workflow execution metrics
    - System health metrics
    """
    
    def __init__(self):
        """Initialize metrics collector"""
        self._initialize_metrics()
        logger.info("MetricsCollector initialized")
    
    def _initialize_metrics(self):
        """Initialize all Prometheus metrics"""
        
        # Task metrics
        self.tasks_total = Counter(
            'orchestrator_tasks_total',
            'Total number of tasks submitted',
            ['task_type', 'status']
        )
        
        self.tasks_duration = Histogram(
            'orchestrator_tasks_duration_seconds',
            'Task execution duration in seconds',
            ['task_type'],
            buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, float('inf'))
        )
        
        # Workflow metrics
        self.workflows_total = Counter(
            'orchestrator_workflows_total',
            'Total number of workflows executed',
            ['workflow_type', 'status']
        )
        
        self.workflow_steps_total = Counter(
            'orchestrator_workflow_steps_total',
            'Total number of workflow steps executed',
            ['step_type', 'status']
        )
        
        self.workflow_duration = Histogram(
            'orchestrator_workflow_duration_seconds',
            'Workflow execution duration in seconds',
            ['workflow_type'],
            buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0, 1800.0, float('inf'))
        )
        
        # Agent metrics
        self.agent_tasks_total = Counter(
            'orchestrator_agent_tasks_total',
            'Total number of tasks executed by agents',
            ['agent_id', 'agent_type', 'status']
        )
        
        self.agent_task_duration = Histogram(
            'orchestrator_agent_task_duration_seconds',
            'Agent task execution duration in seconds',
            ['agent_id', 'agent_type'],
            buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, float('inf'))
        )
        
        self.agent_active_count = Gauge(
            'orchestrator_agents_active',
            'Number of active agents',
            ['agent_type']
        )
        
        # Message broker metrics
        self.messages_sent_total = Counter(
            'orchestrator_messages_sent_total',
            'Total number of messages sent',
            ['message_type', 'from_agent', 'to_agent']
        )
        
        self.messages_received_total = Counter(
            'orchestrator_messages_received_total',
            'Total number of messages received',
            ['message_type', 'agent_id']
        )
        
        self.message_queue_length = Gauge(
            'orchestrator_message_queue_length',
            'Current message queue length',
            ['agent_id']
        )
        
        # State store metrics
        self.state_operations_total = Counter(
            'orchestrator_state_operations_total',
            'Total number of state operations',
            ['operation', 'status']
        )
        
        self.state_store_size = Gauge(
            'orchestrator_state_store_size',
            'Number of workflows with stored state'
        )
        
        # Error metrics
        self.errors_total = Counter(
            'orchestrator_errors_total',
            'Total number of errors',
            ['error_type', 'component']
        )
        
        # Retry metrics
        self.retries_total = Counter(
            'orchestrator_retries_total',
            'Total number of retries',
            ['component', 'status']
        )
        
        # Circuit breaker metrics
        self.circuit_breaker_state = Gauge(
            'orchestrator_circuit_breaker_state',
            'Circuit breaker state (0=closed, 1=open, 2=half_open)',
            ['circuit_name']
        )
        
        self.circuit_breaker_failures = Counter(
            'orchestrator_circuit_breaker_failures_total',
            'Total circuit breaker failures',
            ['circuit_name']
        )
        
        logger.info("Prometheus metrics initialized")
    
    def record_task(
        self,
        task_type: str,
        status: str,
        duration: Optional[float] = None
    ):
        """
        Record task execution metric
        
        Args:
            task_type: Type of task
            status: Task status (completed, failed, etc.)
            duration: Optional execution duration in seconds
        """
        self.tasks_total.labels(task_type=task_type, status=status).inc()
        
        if duration is not None:
            self.tasks_duration.labels(task_type=task_type).observe(duration)
    
    def record_workflow(
        self,
        workflow_type: str,
        status: str,
        duration: Optional[float] = None,
        steps_count: Optional[int] = None
    ):
        """
        Record workflow execution metric
        
        Args:
            workflow_type: Type of workflow
            status: Workflow status
            duration: Optional execution duration
            steps_count: Optional number of steps
        """
        self.workflows_total.labels(workflow_type=workflow_type, status=status).inc()
        
        if duration is not None:
            self.workflow_duration.labels(workflow_type=workflow_type).observe(duration)
    
    def record_workflow_step(
        self,
        step_type: str,
        status: str
    ):
        """Record workflow step execution"""
        self.workflow_steps_total.labels(step_type=step_type, status=status).inc()
    
    def record_agent_task(
        self,
        agent_id: str,
        agent_type: str,
        status: str,
        duration: Optional[float] = None
    ):
        """Record agent task execution"""
        self.agent_tasks_total.labels(
            agent_id=agent_id,
            agent_type=agent_type,
            status=status
        ).inc()
        
        if duration is not None:
            self.agent_task_duration.labels(
                agent_id=agent_id,
                agent_type=agent_type
            ).observe(duration)
    
    def update_agent_count(self, agent_type: str, count: int):
        """Update active agent count"""
        self.agent_active_count.labels(agent_type=agent_type).set(count)
    
    def record_message(
        self,
        message_type: str,
        from_agent: str,
        to_agent: str,
        direction: str = "sent"
    ):
        """Record message metric"""
        if direction == "sent":
            self.messages_sent_total.labels(
                message_type=message_type,
                from_agent=from_agent,
                to_agent=to_agent
            ).inc()
        else:
            self.messages_received_total.labels(
                message_type=message_type,
                agent_id=to_agent
            ).inc()
    
    def update_queue_length(self, agent_id: str, length: int):
        """Update message queue length"""
        self.message_queue_length.labels(agent_id=agent_id).set(length)
    
    def record_state_operation(
        self,
        operation: str,
        status: str
    ):
        """Record state store operation"""
        self.state_operations_total.labels(
            operation=operation,
            status=status
        ).inc()
    
    def update_state_store_size(self, size: int):
        """Update state store size"""
        self.state_store_size.set(size)
    
    def record_error(
        self,
        error_type: str,
        component: str
    ):
        """Record error metric"""
        self.errors_total.labels(
            error_type=error_type,
            component=component
        ).inc()
    
    def record_retry(
        self,
        component: str,
        status: str
    ):
        """Record retry metric"""
        self.retries_total.labels(
            component=component,
            status=status
        ).inc()
    
    def update_circuit_breaker_state(
        self,
        circuit_name: str,
        state: str
    ):
        """Update circuit breaker state metric"""
        state_value = {
            'closed': 0,
            'open': 1,
            'half_open': 2
        }.get(state.lower(), 0)
        
        self.circuit_breaker_state.labels(circuit_name=circuit_name).set(state_value)
    
    def record_circuit_breaker_failure(self, circuit_name: str):
        """Record circuit breaker failure"""
        self.circuit_breaker_failures.labels(circuit_name=circuit_name).inc()
    
    def start_metrics_server(self, port: int = 9090):
        """
        Start Prometheus metrics HTTP server
        
        Args:
            port: Port to serve metrics on
        """
        try:
            start_http_server(port)
            logger.info("Prometheus metrics server started", port=port)
        except Exception as e:
            logger.error("Failed to start metrics server", port=port, error=str(e))
            raise


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector instance"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def start_metrics_server(port: int = 9090):
    """Start metrics server"""
    collector = get_metrics_collector()
    collector.start_metrics_server(port)
