"""
Workflow Recovery
Workflow resume from checkpoints and recovery automation
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from monitoring import get_logger
from orchestrator.planner import WorkflowGraph, WorkflowStep
from orchestrator.executor import WorkflowExecutor, ExecutionContext
from state.snapshot import StateSnapshot, RedisStateSnapshot
from state.store import StateStore
from state.redis_store import RedisStateStore

logger = get_logger(__name__)


class WorkflowRecovery:
    """
    Workflow recovery manager for resuming workflows from checkpoints
    
    Features:
    - Resume workflow from checkpoint
    - Automatic checkpoint creation
    - Recovery automation
    - Workflow state reconstruction
    """
    
    def __init__(
        self,
        executor: WorkflowExecutor,
        state_store: Optional[StateStore] = None,
        snapshot_manager: Optional[StateSnapshot] = None,
        auto_checkpoint: bool = True,
        checkpoint_interval: int = 5  # Checkpoint every N steps
    ):
        """
        Initialize workflow recovery
        
        Args:
            executor: WorkflowExecutor instance
            state_store: StateStore instance
            snapshot_manager: StateSnapshot instance
            auto_checkpoint: Whether to create checkpoints automatically
            checkpoint_interval: Number of steps between auto-checkpoints
        """
        self.executor = executor
        self.state_store = state_store or StateStore()
        self.snapshot_manager = snapshot_manager or StateSnapshot(self.state_store)
        self.auto_checkpoint = auto_checkpoint
        self.checkpoint_interval = checkpoint_interval
        logger.info(
            "WorkflowRecovery initialized",
            auto_checkpoint=auto_checkpoint,
            checkpoint_interval=checkpoint_interval
        )
    
    async def resume_from_checkpoint(
        self,
        checkpoint_id: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Resume workflow execution from checkpoint
        
        Args:
            checkpoint_id: Checkpoint ID to resume from
            options: Optional execution options
            
        Returns:
            Execution result
        """
        logger.info("Resuming workflow from checkpoint", checkpoint_id=checkpoint_id)
        
        # Get checkpoint
        snapshot = self.snapshot_manager.get_checkpoint(checkpoint_id)
        if not snapshot:
            raise ValueError(f"Checkpoint not found: {checkpoint_id}")
        
        workflow_id = snapshot['workflow_id']
        
        # Restore state
        restored_state = self.snapshot_manager.restore_from_checkpoint(
            checkpoint_id,
            restore_state=True
        )
        
        # Reconstruct workflow execution context
        # Note: This is a simplified version - full implementation would need
        # to store workflow graph in checkpoint
        
        logger.info(
            "Workflow state restored",
            checkpoint_id=checkpoint_id,
            workflow_id=workflow_id
        )
        
        return {
            'status': 'resumed',
            'checkpoint_id': checkpoint_id,
            'workflow_id': workflow_id,
            'restored_state': restored_state,
            'message': 'Workflow state restored. Manual workflow reconstruction needed.'
        }
    
    def create_auto_checkpoint(
        self,
        workflow_id: str,
        step_id: str,
        context: ExecutionContext
    ) -> Optional[str]:
        """
        Create automatic checkpoint if conditions met
        
        Args:
            workflow_id: Workflow ID
            step_id: Current step ID
            context: Execution context
            
        Returns:
            Checkpoint ID if created, None otherwise
        """
        if not self.auto_checkpoint:
            return None
        
        # Check if should create checkpoint
        completed_steps = len(context.step_results)
        if completed_steps % self.checkpoint_interval == 0:
            checkpoint_name = f"auto_step_{completed_steps}"
            
            metadata = {
                'step_id': step_id,
                'completed_steps': completed_steps,
                'auto': True
            }
            
            try:
                checkpoint_id = self.snapshot_manager.create_checkpoint(
                    workflow_id,
                    checkpoint_name=checkpoint_name,
                    metadata=metadata
                )
                
                logger.info(
                    "Auto-checkpoint created",
                    checkpoint_id=checkpoint_id,
                    workflow_id=workflow_id,
                    step_id=step_id
                )
                
                return checkpoint_id
            except Exception as e:
                logger.error(
                    "Failed to create auto-checkpoint",
                    workflow_id=workflow_id,
                    error=str(e)
                )
        
        return None
    
    def get_recovery_points(self, workflow_id: str) -> List[Dict[str, Any]]:
        """
        Get all recovery points (checkpoints) for workflow
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            List of checkpoint metadata
        """
        checkpoints = self.snapshot_manager.list_checkpoints(workflow_id)
        
        return [
            {
                'checkpoint_id': cp['checkpoint_id'],
                'checkpoint_name': cp['checkpoint_name'],
                'created_at': cp['created_at'],
                'state_version': cp['state_version'],
                'metadata': cp.get('metadata', {})
            }
            for cp in checkpoints
        ]
    
    async def recover_workflow(
        self,
        workflow_id: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Automatically recover workflow using latest checkpoint
        
        Args:
            workflow_id: Workflow ID
            options: Optional recovery options
            
        Returns:
            Recovery result
        """
        options = options or {}
        
        # Get recovery points
        recovery_points = self.get_recovery_points(workflow_id)
        
        if not recovery_points:
            return {
                'status': 'no_recovery_points',
                'workflow_id': workflow_id,
                'message': 'No checkpoints found for workflow'
            }
        
        # Use latest checkpoint
        latest_checkpoint = recovery_points[0]  # Already sorted by date (newest first)
        checkpoint_id = latest_checkpoint['checkpoint_id']
        
        logger.info(
            "Recovering workflow",
            workflow_id=workflow_id,
            checkpoint_id=checkpoint_id
        )
        
        # Resume from checkpoint
        return await self.resume_from_checkpoint(checkpoint_id, options)


class RecoveryAutomation:
    """Automated recovery mechanisms"""
    
    def __init__(self, recovery: WorkflowRecovery):
        """
        Initialize recovery automation
        
        Args:
            recovery: WorkflowRecovery instance
        """
        self.recovery = recovery
        logger.info("RecoveryAutomation initialized")
    
    async def handle_workflow_failure(
        self,
        workflow_id: str,
        error: Exception,
        context: ExecutionContext,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle workflow failure with automatic recovery
        
        Args:
            workflow_id: Workflow ID
            error: Exception that caused failure
            context: Execution context
            options: Optional recovery options
            
        Returns:
            Recovery action result
        """
        options = options or {}
        auto_recover = options.get('auto_recover', False)
        
        logger.error(
            "Workflow failure detected",
            workflow_id=workflow_id,
            error=str(error),
            auto_recover=auto_recover
        )
        
        # Create checkpoint before recovery attempt
        try:
            checkpoint_name = f"recovery_{datetime.utcnow().timestamp()}"
            checkpoint_id = self.recovery.snapshot_manager.create_checkpoint(
                workflow_id,
                checkpoint_name=checkpoint_name,
                metadata={
                    'failure': True,
                    'error': str(error),
                    'error_type': type(error).__name__,
                    'completed_steps': len(context.step_results)
                }
            )
            
            logger.info(
                "Failure checkpoint created",
                workflow_id=workflow_id,
                checkpoint_id=checkpoint_id
            )
        except Exception as e:
            logger.error(
                "Failed to create failure checkpoint",
                workflow_id=workflow_id,
                error=str(e)
            )
        
        if auto_recover:
            # Attempt automatic recovery
            recovery_result = await self.recovery.recover_workflow(workflow_id, options)
            
            return {
                'status': 'recovery_attempted',
                'workflow_id': workflow_id,
                'recovery_result': recovery_result
            }
        
        return {
            'status': 'failure_recorded',
            'workflow_id': workflow_id,
            'error': str(error),
            'message': 'Manual recovery required'
        }

