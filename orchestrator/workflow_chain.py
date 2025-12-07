"""
Workflow Chain
Support for chaining workflows and agent result passing
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from monitoring import get_logger
from orchestrator.planner import WorkflowGraph, WorkflowStep
from orchestrator.engine import OrchestratorEngine

logger = get_logger(__name__)


class WorkflowChain:
    """
    Workflow chaining support
    
    Allows chaining multiple workflows together where:
    - Output of one workflow becomes input to the next
    - Agent results can be passed between workflows
    - Pipeline pattern support
    """
    
    def __init__(self, orchestrator: OrchestratorEngine):
        """
        Initialize workflow chain
        
        Args:
            orchestrator: OrchestratorEngine instance
        """
        self.orchestrator = orchestrator
        self.chain_history: List[Dict[str, Any]] = []
        logger.info("WorkflowChain initialized")
    
    async def chain_workflows(
        self,
        workflows: List[WorkflowGraph],
        initial_input: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Chain multiple workflows together
        
        Args:
            workflows: List of workflows to chain
            initial_input: Initial input for first workflow
            options: Optional execution options
            
        Returns:
            Final result from last workflow
        """
        options = options or {}
        chain_id = f"chain_{datetime.utcnow().timestamp()}"
        
        logger.info(
            "Starting workflow chain",
            chain_id=chain_id,
            workflows_count=len(workflows)
        )
        
        current_input = initial_input
        chain_results = []
        
        for idx, workflow in enumerate(workflows):
            workflow_id = workflow.workflow_id
            
            logger.info(
                "Executing workflow in chain",
                chain_id=chain_id,
                workflow_index=idx + 1,
                workflow_id=workflow_id
            )
            
            # Create task for workflow
            task = {
                'type': workflow.task_type,
                'input': current_input,
                'workflow': workflow.name
            }
            
            # Execute workflow
            result = await self.orchestrator.execute(task)
            
            if result.get('status') != 'completed':
                logger.error(
                    "Workflow failed in chain",
                    chain_id=chain_id,
                    workflow_id=workflow_id,
                    result=result
                )
                
                return {
                    'status': 'failed',
                    'chain_id': chain_id,
                    'failed_at_workflow': idx,
                    'workflow_id': workflow_id,
                    'result': result,
                    'chain_results': chain_results
                }
            
            # Extract output for next workflow
            workflow_output = result.get('result', {}).get('final_result', {})
            
            # Store chain result
            chain_result = {
                'workflow_index': idx,
                'workflow_id': workflow_id,
                'workflow_name': workflow.name,
                'input': current_input,
                'output': workflow_output,
                'result': result
            }
            chain_results.append(chain_result)
            
            # Prepare input for next workflow
            # Merge workflow output with previous input (can be overridden)
            merge_mode = options.get('merge_mode', 'replace')  # replace, merge, append
            if merge_mode == 'merge':
                current_input = {**current_input, **workflow_output}
            elif merge_mode == 'append':
                if isinstance(current_input, dict) and isinstance(workflow_output, dict):
                    current_input = {**current_input, **workflow_output}
                elif isinstance(current_input, list):
                    current_input.append(workflow_output)
                else:
                    current_input = [current_input, workflow_output]
            else:  # replace
                current_input = workflow_output
        
        final_result = {
            'status': 'completed',
            'chain_id': chain_id,
            'final_result': current_input,
            'chain_results': chain_results,
            'workflows_count': len(workflows)
        }
        
        logger.info(
            "Workflow chain completed",
            chain_id=chain_id,
            workflows_count=len(workflows)
        )
        
        return final_result
    
    async def create_pipeline(
        self,
        workflow_templates: List[Dict[str, Any]],
        input_data: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create and execute a pipeline from workflow templates
        
        Args:
            workflow_templates: List of workflow template configurations
            input_data: Input data for pipeline
            options: Optional execution options
            
        Returns:
            Pipeline execution result
        """
        # Create workflows from templates
        workflows = []
        for template in workflow_templates:
            # Create workflow from template
            workflow = await self.orchestrator.planner.plan({
                'type': template.get('type', 'unknown'),
                'input': template.get('input', {})
            })
            workflows.append(workflow)
        
        # Execute chain
        return await self.chain_workflows(workflows, input_data, options)
    
    def get_chain_history(self) -> List[Dict[str, Any]]:
        """Get chain execution history"""
        return self.chain_history.copy()


class AgentResultPasser:
    """
    Helper for passing agent results between workflows
    """
    
    @staticmethod
    def extract_agent_result(
        workflow_result: Dict[str, Any],
        agent_id: Optional[str] = None,
        step_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Extract agent result from workflow result
        
        Args:
            workflow_result: Workflow execution result
            agent_id: Optional agent ID to filter by
            step_id: Optional step ID to get specific result
            
        Returns:
            Agent result or None
        """
        steps = workflow_result.get('steps', {})
        
        if step_id:
            return steps.get(step_id)
        
        # Get all step results
        if steps:
            # Return last step result if no filter
            step_ids = list(steps.keys())
            if step_ids:
                return steps[step_ids[-1]]
        
        # Try to get from final_result
        final_result = workflow_result.get('result', {}).get('final_result', {})
        if final_result:
            return final_result
        
        return None
    
    @staticmethod
    def prepare_next_input(
        previous_result: Dict[str, Any],
        mapping: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Prepare input for next workflow from previous result
        
        Args:
            previous_result: Previous workflow result
            mapping: Optional field mapping (old_field -> new_field)
            
        Returns:
            Prepared input dictionary
        """
        if mapping:
            # Map fields according to mapping
            next_input = {}
            for old_field, new_field in mapping.items():
                if old_field in previous_result:
                    next_input[new_field] = previous_result[old_field]
            return next_input
        
        # Use result as-is
        return previous_result

