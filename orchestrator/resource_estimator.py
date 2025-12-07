"""
Resource Estimation
Estimates resource requirements for tasks and workflows
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from monitoring import get_logger

logger = get_logger(__name__)


class ResourceEstimate:
    """Resource estimation result"""
    
    def __init__(
        self,
        estimated_time: int,
        estimated_cost: float,
        required_agents: List[str],
        required_capabilities: List[str],
        memory_estimate: Optional[int] = None,
        cpu_estimate: Optional[float] = None
    ):
        self.estimated_time = estimated_time  # seconds
        self.estimated_cost = estimated_cost
        self.required_agents = required_agents
        self.required_capabilities = required_capabilities
        self.memory_estimate = memory_estimate  # MB
        self.cpu_estimate = cpu_estimate  # CPU cores
        self.created_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'estimated_time_seconds': self.estimated_time,
            'estimated_time_formatted': str(timedelta(seconds=self.estimated_time)),
            'estimated_cost': self.estimated_cost,
            'required_agents': self.required_agents,
            'required_capabilities': self.required_capabilities,
            'memory_estimate_mb': self.memory_estimate,
            'cpu_estimate': self.cpu_estimate,
            'created_at': self.created_at.isoformat()
        }


class ResourceEstimator:
    """Estimates resource requirements for workflows"""
    
    # Default cost per second for different agent types
    AGENT_COSTS = {
        'research_agent': 0.0001,
        'analysis_agent': 0.00005,
        'code_generation_agent': 0.0002,
        'validation_agent': 0.00003,
        'generic_agent': 0.00005,
        'synthesis_agent': 0.00008,
        'requirements_agent': 0.00005,
        'transformation_agent': 0.00005,
        'aggregation_agent': 0.00003
    }
    
    # Default time estimates (seconds) for different agent types
    AGENT_TIME_ESTIMATES = {
        'research_agent': 60,
        'analysis_agent': 30,
        'code_generation_agent': 120,
        'validation_agent': 20,
        'generic_agent': 10,
        'synthesis_agent': 45,
        'requirements_agent': 30,
        'transformation_agent': 30,
        'aggregation_agent': 20
    }
    
    def __init__(self):
        """Initialize resource estimator"""
        logger.info("ResourceEstimator initialized")
    
    def estimate_workflow(
        self,
        workflow: 'WorkflowGraph'
    ) -> ResourceEstimate:
        """
        Estimate resources for a workflow
        
        Args:
            workflow: WorkflowGraph to estimate
            
        Returns:
            ResourceEstimate object
        """
        total_time = 0
        total_cost = 0.0
        required_agents = set()
        required_capabilities = set()
        
        # Calculate parallel groups for accurate time estimation
        parallel_groups = workflow.get_parallel_groups()
        
        # Estimate time: sum of parallel group max times
        for group in parallel_groups:
            group_max_time = 0
            for step_id in group:
                step = workflow.get_step(step_id)
                if step:
                    step_time = self._estimate_step_time(step)
                    group_max_time = max(group_max_time, step_time)
                    total_cost += self._estimate_step_cost(step)
                    
                    required_agents.add(step.agent_type)
                    
                    # Get capabilities from step metadata if available
                    if hasattr(step, 'capabilities_required'):
                        required_capabilities.update(step.capabilities_required)
            
            total_time += group_max_time
        
        logger.info(
            "Workflow resource estimated",
            workflow_id=workflow.workflow_id,
            estimated_time=total_time,
            estimated_cost=total_cost
        )
        
        return ResourceEstimate(
            estimated_time=total_time,
            estimated_cost=round(total_cost, 4),
            required_agents=list(required_agents),
            required_capabilities=list(required_capabilities),
            memory_estimate=self._estimate_memory(workflow),
            cpu_estimate=self._estimate_cpu(workflow)
        )
    
    def estimate_step(self, step: 'WorkflowStep') -> ResourceEstimate:
        """
        Estimate resources for a single step
        
        Args:
            step: WorkflowStep to estimate
            
        Returns:
            ResourceEstimate object
        """
        time = self._estimate_step_time(step)
        cost = self._estimate_step_cost(step)
        
        capabilities = []
        if hasattr(step, 'capabilities_required'):
            capabilities = step.capabilities_required
        
        return ResourceEstimate(
            estimated_time=time,
            estimated_cost=cost,
            required_agents=[step.agent_type],
            required_capabilities=capabilities
        )
    
    def _estimate_step_time(self, step: 'WorkflowStep') -> int:
        """Estimate time for a step"""
        # Check if step has explicit time estimate
        if hasattr(step, 'estimated_time') and step.estimated_time:
            return step.estimated_time
        
        # Use default estimates based on agent type
        return self.AGENT_TIME_ESTIMATES.get(
            step.agent_type,
            self.AGENT_TIME_ESTIMATES['generic_agent']
        )
    
    def _estimate_step_cost(self, step: 'WorkflowStep') -> float:
        """Estimate cost for a step"""
        time = self._estimate_step_time(step)
        
        # Check if step has explicit cost estimate
        if hasattr(step, 'estimated_cost') and step.estimated_cost:
            return step.estimated_cost
        
        # Calculate cost based on time and agent type
        cost_per_second = self.AGENT_COSTS.get(
            step.agent_type,
            self.AGENT_COSTS['generic_agent']
        )
        
        return time * cost_per_second
    
    def _estimate_memory(self, workflow: 'WorkflowGraph') -> int:
        """Estimate memory requirements in MB"""
        # Base memory per step
        base_memory_per_step = 100  # MB
        
        # Estimate based on number of steps
        return len(workflow.steps) * base_memory_per_step
    
    def _estimate_cpu(self, workflow: 'WorkflowGraph') -> float:
        """Estimate CPU requirements in cores"""
        # Get parallel groups to estimate max concurrent tasks
        parallel_groups = workflow.get_parallel_groups()
        max_parallel = max(len(group) for group in parallel_groups) if parallel_groups else 1
        
        # Each agent needs ~0.5 CPU cores
        return max_parallel * 0.5
    
    def estimate_task(self, task: Dict[str, Any]) -> ResourceEstimate:
        """
        Quick estimate for a task (without full workflow planning)
        
        Args:
            task: Task dictionary
            
        Returns:
            ResourceEstimate object
        """
        task_type = task.get('type', 'unknown')
        
        # Use default estimates based on task type
        default_time = 30  # seconds
        default_cost = 0.01
        
        if 'research' in task_type.lower():
            default_time = 60
            default_cost = 0.02
        elif 'code' in task_type.lower() or 'generate' in task_type.lower():
            default_time = 120
            default_cost = 0.05
        elif 'analyze' in task_type.lower():
            default_time = 30
            default_cost = 0.01
        
        return ResourceEstimate(
            estimated_time=default_time,
            estimated_cost=default_cost,
            required_agents=['generic_agent'],
            required_capabilities=[task_type]
        )

