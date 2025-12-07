"""
Workflow Executor
Executes workflows using selected agents
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
from monitoring import get_logger
from orchestrator.planner import WorkflowGraph, WorkflowStep
from orchestrator.selector import AgentSelector
from agents.registry import AgentRegistry

logger = get_logger(__name__)


class ExecutionContext:
    """Context for workflow execution"""
    
    def __init__(self, workflow: WorkflowGraph):
        self.workflow = workflow
        self.step_results: Dict[str, Any] = {}
        self.current_step: Optional[str] = None
        self.errors: List[Dict[str, Any]] = []
        self.start_time = datetime.utcnow()
        self.state: Dict[str, Any] = {}
    
    def set_step_result(self, step_id: str, result: Any):
        """Set result for a step"""
        self.step_results[step_id] = result
    
    def get_step_result(self, step_id: str) -> Optional[Any]:
        """Get result for a step"""
        return self.step_results.get(step_id)
    
    def add_error(self, step_id: str, error: Exception):
        """Add error to context"""
        self.errors.append({
            'step_id': step_id,
            'error': str(error),
            'error_type': type(error).__name__,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    def get_state(self) -> Dict[str, Any]:
        """Get current execution state"""
        return {
            'workflow_id': self.workflow.workflow_id,
            'current_step': self.current_step,
            'completed_steps': list(self.step_results.keys()),
            'errors': self.errors,
            'state': self.state,
            'elapsed_time': (datetime.utcnow() - self.start_time).total_seconds()
        }


class WorkflowExecutor:
    """Executes workflows using selected agents"""
    
    def __init__(self, registry: AgentRegistry, selector: AgentSelector):
        """
        Initialize workflow executor
        
        Args:
            registry: AgentRegistry instance
            selector: AgentSelector instance
        """
        self.registry = registry
        self.selector = selector
        self.execution_contexts: Dict[str, ExecutionContext] = {}
        logger.info("WorkflowExecutor initialized")
    
    async def execute(
        self,
        workflow: WorkflowGraph,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a workflow
        
        Args:
            workflow: WorkflowGraph to execute
            options: Optional execution options
            
        Returns:
            Execution result dictionary
        """
        options = options or {}
        
        logger.info(
            "Starting workflow execution",
            workflow_id=workflow.workflow_id,
            steps_count=len(workflow.steps)
        )
        
        # Create execution context
        context = ExecutionContext(workflow)
        self.execution_contexts[workflow.workflow_id] = context
        
        try:
            # Calculate execution order if not already done
            if not workflow.execution_order:
                workflow.calculate_execution_order()
            
            # Execute steps in order
            results = await self._execute_steps(workflow, context, options)
            
            # Aggregate results
            final_result = self._aggregate_results(context, results)
            
            logger.info(
                "Workflow execution completed",
                workflow_id=workflow.workflow_id,
                success=True
            )
            
            return {
                'status': 'completed',
                'workflow_id': workflow.workflow_id,
                'result': final_result,
                'steps': {step_id: context.get_step_result(step_id) 
                         for step_id in workflow.execution_order},
                'execution_time': (datetime.utcnow() - context.start_time).total_seconds()
            }
            
        except Exception as e:
            logger.error(
                "Workflow execution failed",
                workflow_id=workflow.workflow_id,
                error=str(e),
                exc_info=True
            )
            
            return {
                'status': 'failed',
                'workflow_id': workflow.workflow_id,
                'error': str(e),
                'errors': context.errors,
                'execution_time': (datetime.utcnow() - context.start_time).total_seconds()
            }
    
    async def _execute_steps(
        self,
        workflow: WorkflowGraph,
        context: ExecutionContext,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute workflow steps"""
        results = {}
        
        for step_id in workflow.execution_order:
            step = workflow.get_step(step_id)
            if not step:
                logger.warning("Step not found", step_id=step_id)
                continue
            
            context.current_step = step_id
            
            try:
                # Check if step should be executed (conditional routing)
                if not self._should_execute_step(step, context):
                    logger.info("Step skipped due to condition", step_id=step_id)
                    continue
                
                # Prepare step input
                step_input = self._prepare_step_input(step, context)
                
                # Select agent for step
                agent = await self.selector.select_for_step(step, options)
                
                if not agent:
                    raise ValueError(f"No suitable agent found for step {step_id}")
                
                # Execute step
                logger.info(
                    "Executing step",
                    step_id=step_id,
                    agent_id=agent.agent_id
                )
                
                # Track workload
                self.selector.increment_workload(agent.agent_id)
                
                try:
                    step.status = 'in_progress'
                    
                    # Execute agent
                    result = await agent.execute(step_input)
                    
                    step.status = 'completed'
                    step.result = result
                    
                    # Store result
                    context.set_step_result(step_id, result)
                    
                    if step.output_key:
                        context.state[step.output_key] = result
                    
                    results[step_id] = result
                    
                    logger.info("Step completed", step_id=step_id)
                    
                finally:
                    # Decrement workload
                    self.selector.decrement_workload(agent.agent_id)
                
            except Exception as e:
                step.status = 'failed'
                context.add_error(step_id, e)
                logger.error(
                    "Step execution failed",
                    step_id=step_id,
                    error=str(e)
                )
                
                # Check if we should continue on error
                if not options.get('continue_on_error', False):
                    raise
        
        return results
    
    def _should_execute_step(self, step: WorkflowStep, context: ExecutionContext) -> bool:
        """Check if step should be executed based on condition"""
        if not step.condition:
            return True
        
        condition = step.condition
        condition_type = condition.get('type')
        field = condition.get('field')
        operator = condition.get('operator')
        value = condition.get('value')
        
        if not field:
            return True
        
        # Evaluate condition from context state
        field_value = self._get_field_value(field, context)
        
        if operator == 'equals':
            return field_value == value
        elif operator == 'not_equals':
            return field_value != value
        elif operator == 'greater_than':
            return field_value > value
        elif operator == 'less_than':
            return field_value < value
        elif operator == 'contains':
            return value in field_value if isinstance(field_value, (list, str)) else False
        
        return True
    
    def _get_field_value(self, field: str, context: ExecutionContext) -> Any:
        """Get field value from context"""
        # Support dot notation for nested fields
        parts = field.split('.')
        value = context.state
        
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
        
        return value
    
    def _prepare_step_input(self, step: WorkflowStep, context: ExecutionContext) -> Dict[str, Any]:
        """Prepare input data for step execution"""
        input_data = step.input_data.copy()
        
        # Resolve dependencies - merge results from dependent steps
        for dep_step_id in step.depends_on:
            dep_result = context.get_step_result(dep_step_id)
            if dep_result:
                # Merge dependency result into input
                if isinstance(dep_result, dict):
                    input_data.update(dep_result)
                else:
                    input_data[f'{dep_step_id}_result'] = dep_result
        
        # Resolve template variables (e.g., {{step.result.field}})
        input_data = self._resolve_template_variables(input_data, context)
        
        return input_data
    
    def _resolve_template_variables(
        self,
        data: Any,
        context: ExecutionContext
    ) -> Any:
        """Resolve template variables in data"""
        if isinstance(data, dict):
            return {k: self._resolve_template_variables(v, context) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._resolve_template_variables(item, context) for item in data]
        elif isinstance(data, str) and data.startswith('{{') and data.endswith('}}'):
            # Extract field path
            field_path = data[2:-2].strip()
            return self._get_field_value(field_path, context) or data
        else:
            return data
    
    def _aggregate_results(
        self,
        context: ExecutionContext,
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Aggregate results from all steps"""
        if not results:
            return {}
        
        # Get final step result (last in execution order)
        workflow = context.workflow
        if workflow.execution_order:
            final_step_id = workflow.execution_order[-1]
            final_result = results.get(final_step_id, {})
            
            return {
                'final_result': final_result,
                'all_results': results,
                'state': context.state
            }
        
        return {'all_results': results, 'state': context.state}
    
    def get_execution_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get execution status for a workflow"""
        context = self.execution_contexts.get(workflow_id)
        if not context:
            return None
        
        return context.get_state()
