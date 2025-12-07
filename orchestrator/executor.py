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
            
            # Execute steps (parallel if enabled)
            enable_parallel = options.get('enable_parallel', True)
            if enable_parallel:
                results = await self._execute_steps_parallel(workflow, context, options)
            else:
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
    
    async def _execute_steps_parallel(
        self,
        workflow: WorkflowGraph,
        context: ExecutionContext,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute workflow steps in parallel where possible
        
        Args:
            workflow: WorkflowGraph to execute
            context: Execution context
            options: Execution options
            
        Returns:
            Dictionary of step results
        """
        results = {}
        
        # Get parallel groups
        parallel_groups = workflow.get_parallel_groups()
        
        logger.info(
            "Executing workflow in parallel",
            workflow_id=workflow.workflow_id,
            parallel_groups_count=len(parallel_groups)
        )
        
        # Execute groups sequentially, steps within group in parallel
        for group_idx, group in enumerate(parallel_groups):
            logger.info(
                "Executing parallel group",
                group_idx=group_idx,
                step_ids=group
            )
            
            # Execute all steps in this group in parallel
            group_tasks = []
            for step_id in group:
                step = workflow.get_step(step_id)
                if not step:
                    logger.warning("Step not found", step_id=step_id)
                    continue
                
                # Create task for this step
                task = self._execute_single_step(step, context, options)
                group_tasks.append((step_id, task))
            
            # Wait for all tasks in group to complete
            group_results = await asyncio.gather(
                *[task for _, task in group_tasks],
                return_exceptions=True
            )
            
            # Process results
            for (step_id, _), result in zip(group_tasks, group_results):
                if isinstance(result, Exception):
                    # Error occurred
                    step = workflow.get_step(step_id)
                    if step:
                        step.status = 'failed'
                        context.add_error(step_id, result)
                    
                    logger.error(
                        "Step execution failed in parallel group",
                        step_id=step_id,
                        error=str(result)
                    )
                    
                    if not options.get('continue_on_error', False):
                        raise result
                else:
                    # Success
                    if result:
                        results[step_id] = result
            
            # Check if we should stop on error
            if not options.get('continue_on_error', False):
                failed_steps = [
                    step_id for step_id in group
                    if workflow.get_step(step_id) and
                    workflow.get_step(step_id).status == 'failed'
                ]
                if failed_steps:
                    raise Exception(f"Steps failed: {failed_steps}")
        
        return results
    
    async def _execute_single_step(
        self,
        step: WorkflowStep,
        context: ExecutionContext,
        options: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Execute a single step (used for parallel execution)
        
        Args:
            step: WorkflowStep to execute
            context: Execution context
            options: Execution options
            
        Returns:
            Step result or None if skipped
        """
        step_id = step.step_id
        
        try:
            # Check if step should be executed (conditional routing)
            if not self._should_execute_step(step, context):
                logger.info("Step skipped due to condition", step_id=step_id)
                step.status = 'skipped'
                return None
            
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
                
                # Store result (with thread-safe access for parallel execution)
                context.set_step_result(step_id, result)
                
                if step.output_key:
                    context.state[step.output_key] = result
                
                logger.info("Step completed", step_id=step_id)
                
                return result
                
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
            raise
    
    def _should_execute_step(self, step: WorkflowStep, context: ExecutionContext) -> bool:
        """
        Check if step should be executed based on condition
        
        Supports:
        - Simple conditions: field operator value
        - Complex conditions: AND/OR logic
        - Branching: multiple conditions with else
        """
        if not step.condition:
            return True
        
        condition = step.condition
        condition_type = condition.get('type', 'simple')
        
        if condition_type == 'simple':
            return self._evaluate_simple_condition(condition, context)
        elif condition_type == 'and':
            # AND logic: all conditions must be true
            conditions = condition.get('conditions', [])
            return all(self._evaluate_simple_condition(c, context) for c in conditions)
        elif condition_type == 'or':
            # OR logic: at least one condition must be true
            conditions = condition.get('conditions', [])
            return any(self._evaluate_simple_condition(c, context) for c in conditions)
        elif condition_type == 'branch':
            # Branching: evaluate branch conditions
            branches = condition.get('branches', [])
            for branch in branches:
                branch_condition = branch.get('condition')
                if branch_condition and self._evaluate_simple_condition(branch_condition, context):
                    # This branch matches, check if this step is in this branch
                    branch_steps = branch.get('steps', [])
                    return step.step_id in branch_steps
            
            # Check else branch
            else_branch = condition.get('else')
            if else_branch:
                else_steps = else_branch.get('steps', [])
                return step.step_id in else_steps
            
            return False
        
        return True
    
    def _evaluate_simple_condition(
        self,
        condition: Dict[str, Any],
        context: ExecutionContext
    ) -> bool:
        """Evaluate a simple condition"""
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
        elif operator == 'greater_than_or_equal':
            return field_value >= value
        elif operator == 'less_than_or_equal':
            return field_value <= value
        elif operator == 'contains':
            return value in field_value if isinstance(field_value, (list, str)) else False
        elif operator == 'not_contains':
            return value not in field_value if isinstance(field_value, (list, str)) else True
        elif operator == 'exists':
            return field_value is not None
        elif operator == 'not_exists':
            return field_value is None
        elif operator == 'in':
            return field_value in value if isinstance(value, (list, tuple, set)) else False
        elif operator == 'not_in':
            return field_value not in value if isinstance(value, (list, tuple, set)) else True
        elif operator == 'regex':
            import re
            pattern = re.compile(value) if isinstance(value, str) else value
            return bool(pattern.match(str(field_value))) if field_value else False
        
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
        results: Dict[str, Any],
        aggregation_mode: str = 'final'
    ) -> Dict[str, Any]:
        """
        Aggregate results from all steps
        
        Args:
            context: Execution context
            results: Step results dictionary
            aggregation_mode: Aggregation mode ('final', 'all', 'merge', 'fan_in')
            
        Returns:
            Aggregated results
        """
        if not results:
            return {}
        
        workflow = context.workflow
        
        if aggregation_mode == 'final':
            # Get final step result (last in execution order)
            if workflow.execution_order:
                final_step_id = workflow.execution_order[-1]
                final_result = results.get(final_step_id, {})
                
                return {
                    'final_result': final_result,
                    'all_results': results,
                    'state': context.state
                }
        
        elif aggregation_mode == 'all':
            # Return all results
            return {
                'all_results': results,
                'state': context.state
            }
        
        elif aggregation_mode == 'merge':
            # Merge all results into single dictionary
            merged = {}
            for step_id, result in results.items():
                if isinstance(result, dict):
                    merged.update(result)
                else:
                    merged[step_id] = result
            
            return {
                'merged_result': merged,
                'all_results': results,
                'state': context.state
            }
        
        elif aggregation_mode == 'fan_in':
            # Fan-in: collect results from parallel steps
            # Group results by step output_key or step_id
            fan_in_results = {}
            
            for step_id, result in results.items():
                step = workflow.get_step(step_id)
                if step and step.output_key:
                    key = step.output_key
                else:
                    key = step_id
                
                if key not in fan_in_results:
                    fan_in_results[key] = []
                
                fan_in_results[key].append(result)
            
            return {
                'fan_in_results': fan_in_results,
                'all_results': results,
                'state': context.state
            }
        
        # Default: return all results
        return {'all_results': results, 'state': context.state}
    
    async def _fan_out_execution(
        self,
        step: WorkflowStep,
        fan_out_data: List[Any],
        context: ExecutionContext,
        options: Dict[str, Any]
    ) -> List[Any]:
        """
        Execute fan-out pattern: execute same step with multiple inputs
        
        Args:
            step: WorkflowStep template
            fan_out_data: List of input data for each parallel execution
            context: Execution context
            options: Execution options
            
        Returns:
            List of results from all parallel executions
        """
        logger.info(
            "Executing fan-out",
            step_id=step.step_id,
            fan_out_count=len(fan_out_data)
        )
        
        # Create tasks for each fan-out item
        tasks = []
        for idx, item_data in enumerate(fan_out_data):
            # Create a copy of step for this fan-out item
            fan_step = WorkflowStep(
                step_id=f"{step.step_id}_fan_{idx}",
                agent_type=step.agent_type,
                input_data={**step.input_data, **item_data} if isinstance(item_data, dict) else item_data,
                depends_on=step.depends_on,
                output_key=f"{step.output_key}_{idx}" if step.output_key else None,
                condition=step.condition
            )
            
            task = self._execute_single_step(fan_step, context, options)
            tasks.append(task)
        
        # Execute all fan-out tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and return successful results
        successful_results = []
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    "Fan-out item failed",
                    step_id=step.step_id,
                    item_index=idx,
                    error=str(result)
                )
                if not options.get('continue_on_error', False):
                    raise result
            else:
                successful_results.append(result)
        
        return successful_results
    
    def get_execution_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get execution status for a workflow"""
        context = self.execution_contexts.get(workflow_id)
        if not context:
            return None
        
        return context.get_state()
