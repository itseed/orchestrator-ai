"""
Task Planner
Plans and decomposes tasks into workflows
"""

from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from monitoring import get_logger
from orchestrator.templates import WORKFLOW_TEMPLATES, match_template, get_template

logger = get_logger(__name__)


class WorkflowStep:
    """Represents a single step in a workflow"""
    
    def __init__(
        self,
        step_id: str,
        agent_type: str,
        input_data: Optional[Dict[str, Any]] = None,
        depends_on: Optional[List[str]] = None,
        output_key: Optional[str] = None,
        condition: Optional[Dict[str, Any]] = None
    ):
        self.step_id = step_id
        self.agent_type = agent_type
        self.input_data = input_data or {}
        self.depends_on = depends_on or []
        self.output_key = output_key
        self.condition = condition
        self.status = 'pending'
        self.result: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert step to dictionary"""
        return {
            'step_id': self.step_id,
            'agent_type': self.agent_type,
            'input_data': self.input_data,
            'depends_on': self.depends_on,
            'output_key': self.output_key,
            'condition': self.condition,
            'status': self.status
        }


class WorkflowGraph:
    """Represents a workflow graph with steps and dependencies"""
    
    def __init__(self, workflow_id: str, name: str, task_type: str):
        self.workflow_id = workflow_id
        self.name = name
        self.task_type = task_type
        self.steps: Dict[str, WorkflowStep] = {}
        self.execution_order: List[str] = []
        self.created_at = datetime.utcnow()
    
    def add_step(self, step: WorkflowStep):
        """Add a step to the workflow"""
        self.steps[step.step_id] = step
    
    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        """Get a step by ID"""
        return self.steps.get(step_id)
    
    def calculate_execution_order(self) -> List[str]:
        """
        Calculate the execution order based on dependencies (topological sort)
        
        Returns:
            List of step IDs in execution order
        """
        # Build dependency graph
        in_degree: Dict[str, int] = {step_id: 0 for step_id in self.steps}
        
        for step in self.steps.values():
            for dep in step.depends_on:
                if dep in in_degree:
                    in_degree[step.step_id] += 1
        
        # Topological sort
        queue: List[str] = [step_id for step_id, degree in in_degree.items() if degree == 0]
        execution_order: List[str] = []
        
        while queue:
            step_id = queue.pop(0)
            execution_order.append(step_id)
            
            # Reduce in-degree for dependent steps
            for step in self.steps.values():
                if step_id in step.depends_on:
                    in_degree[step.step_id] -= 1
                    if in_degree[step.step_id] == 0:
                        queue.append(step.step_id)
        
        # Check for circular dependencies
        if len(execution_order) != len(self.steps):
            raise ValueError("Circular dependency detected in workflow")
        
        self.execution_order = execution_order
        return execution_order
    
    def get_parallel_groups(self) -> List[List[str]]:
        """
        Group steps that can be executed in parallel
        
        Returns:
            List of groups, each group contains step IDs that can run in parallel
        """
        if not self.execution_order:
            self.calculate_execution_order()
        
        # Build reverse dependency map
        depends_on_map: Dict[str, Set[str]] = {
            step_id: set(step.depends_on) for step_id, step in self.steps.items()
        }
        
        completed: Set[str] = set()
        parallel_groups: List[List[str]] = []
        
        for step_id in self.execution_order:
            step = self.steps[step_id]
            
            # Check if all dependencies are completed
            if all(dep in completed for dep in step.depends_on):
                # Find or create a parallel group
                added = False
                for group in parallel_groups:
                    # Check if this step can run in parallel with group members
                    can_parallel = True
                    for group_step_id in group:
                        group_step = self.steps[group_step_id]
                        # Check for conflicts
                        if step_id in group_step.depends_on or group_step_id in step.depends_on:
                            can_parallel = False
                            break
                    
                    if can_parallel:
                        group.append(step_id)
                        added = True
                        break
                
                if not added:
                    parallel_groups.append([step_id])
                
                completed.add(step_id)
        
        return parallel_groups
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow graph to dictionary"""
        return {
            'workflow_id': self.workflow_id,
            'name': self.name,
            'task_type': self.task_type,
            'steps': {step_id: step.to_dict() for step_id, step in self.steps.items()},
            'execution_order': self.execution_order,
            'created_at': self.created_at.isoformat()
        }


class TaskPlanner:
    """Plans and decomposes tasks into workflows"""
    
    def __init__(self):
        """Initialize task planner"""
        self.workflow_templates: Dict[str, Dict[str, Any]] = {}
        self._load_default_templates()
        logger.info("TaskPlanner initialized")
    
    async def estimate_resources(self, workflow: WorkflowGraph) -> Dict[str, Any]:
        """
        Estimate resource requirements for a workflow
        
        Args:
            workflow: WorkflowGraph to estimate
            
        Returns:
            Resource estimation dictionary
        """
        from orchestrator.resource_estimator import ResourceEstimator
        
        estimator = ResourceEstimator()
        estimate = estimator.estimate_workflow(workflow)
        
        return estimate.to_dict()
    
    def _load_default_templates(self):
        """Load default workflow templates from templates module"""
        self.workflow_templates = WORKFLOW_TEMPLATES.copy()
        logger.info("Default workflow templates loaded", count=len(self.workflow_templates))
    
    async def plan(self, task: Dict[str, Any]) -> WorkflowGraph:
        """
        Create a workflow plan from task
        
        Args:
            task: Task dictionary with type and input
            
        Returns:
            WorkflowGraph representing the planned workflow
        """
        import uuid
        
        task_type = task.get('type', 'unknown')
        workflow_id = str(uuid.uuid4())
        workflow_name = f"{task_type}_workflow_{workflow_id[:8]}"
        
        logger.info(
            "Planning workflow",
            task_type=task_type,
            workflow_id=workflow_id
        )
        
        # Create workflow graph
        workflow = WorkflowGraph(workflow_id, workflow_name, task_type)
        
        # Decompose task into steps
        steps = await self._decompose_task(task)
        
        # Add steps to workflow
        for step_data in steps:
            step = WorkflowStep(
                step_id=step_data['step_id'],
                agent_type=step_data['agent_type'],
                input_data=step_data.get('input_data', task.get('input', {})),
                depends_on=step_data.get('depends_on', []),
                output_key=step_data.get('output_key'),
                condition=step_data.get('condition')
            )
            workflow.add_step(step)
        
        # Calculate execution order
        workflow.calculate_execution_order()
        
        logger.info(
            "Workflow planned",
            workflow_id=workflow_id,
            steps_count=len(workflow.steps),
            execution_order=workflow.execution_order
        )
        
        return workflow
    
    async def _decompose_task(self, task: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Decompose task into workflow steps
        
        Args:
            task: Task dictionary
            
        Returns:
            List of step dictionaries
        """
        task_type = task.get('type', 'unknown')
        
        # Match template
        template_name = match_template(task_type)
        
        if template_name and template_name in self.workflow_templates:
            template = self.workflow_templates[template_name]
            steps = template['steps'].copy()
            
            # Merge input data into steps
            input_data = task.get('input', {})
            for step in steps:
                if 'input_data' not in step:
                    step['input_data'] = input_data
            
            logger.debug("Matched template", task_type=task_type, template=template_name)
            return steps
        
        # Default: single step workflow
        logger.warning("No template matched, using default", task_type=task_type)
        return [{
            'step_id': 'execute',
            'agent_type': 'generic_agent',
            'depends_on': [],
            'input_data': task.get('input', {})
        }]
    
    async def _analyze_dependencies(self, steps: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Analyze dependencies between steps
        
        Args:
            steps: List of step dictionaries
            
        Returns:
            Dependency graph as dictionary
        """
        dependencies: Dict[str, List[str]] = {}
        
        for step in steps:
            step_id = step['step_id']
            depends_on = step.get('depends_on', [])
            dependencies[step_id] = depends_on
        
        return dependencies
    
    def register_template(self, template_name: str, template: Dict[str, Any]):
        """
        Register a custom workflow template
        
        Args:
            template_name: Name of the template
            template: Template dictionary with steps
        """
        self.workflow_templates[template_name] = template
        logger.info("Workflow template registered", template_name=template_name)
    
    def get_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a workflow template
        
        Args:
            template_name: Name of the template
            
        Returns:
            Template dictionary or None
        """
        return self.workflow_templates.get(template_name)
