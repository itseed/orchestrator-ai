"""
Orchestrator Engine
Core engine for managing AI agents and workflows
"""

import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from monitoring import get_logger
from orchestrator.planner import TaskPlanner, WorkflowGraph
from orchestrator.selector import AgentSelector
from orchestrator.executor import WorkflowExecutor
from agents.registry import AgentRegistry
from state.store import StateStore

logger = get_logger(__name__)


class OrchestratorEngine:
    """Core Orchestrator Engine for managing AI agents"""
    
    def __init__(
        self,
        registry: Optional[AgentRegistry] = None,
        state_store: Optional[StateStore] = None
    ):
        """
        Initialize orchestrator engine
        
        Args:
            registry: Optional AgentRegistry instance (creates new if not provided)
            state_store: Optional StateStore instance (creates new if not provided)
        """
        self.registry = registry or AgentRegistry()
        self.state_store = state_store or StateStore()
        self.selector = AgentSelector(self.registry)
        self.planner = TaskPlanner()
        self.executor = WorkflowExecutor(self.registry, self.selector)
        
        # Task management
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.task_queue: list = []
        
        logger.info("OrchestratorEngine initialized")
    
    async def execute(self, task: Dict[str, Any], task_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute a task through the orchestrator
        
        Args:
            task: Task dictionary with type and input
            task_id: Optional task ID (generates new if not provided)
            
        Returns:
            Task execution result
        """
        # Use provided task_id or generate new one
        if task_id is None:
            task_id = str(uuid.uuid4())
        
        logger.info("Task submitted", task_id=task_id, task_type=task.get('type'))
        
        # Create task record
        self.tasks[task_id] = {
            'task_id': task_id,
            'status': 'pending',
            'input': task,
            'workflow_id': None,
            'created_at': datetime.utcnow().isoformat(),
            'result': None,
            'error': None
        }
        
        try:
            # Update status
            self.tasks[task_id]['status'] = 'planning'
            
            # Step 1: Plan the task
            workflow = await self.planner.plan(task)
            self.tasks[task_id]['workflow_id'] = workflow.workflow_id
            self.tasks[task_id]['status'] = 'planning_complete'
            
            logger.info(
                "Workflow planned",
                task_id=task_id,
                workflow_id=workflow.workflow_id,
                steps_count=len(workflow.steps)
            )
            
            # Save initial state
            self.state_store.save_state(
                workflow.workflow_id,
                {'task_id': task_id, 'status': 'planning_complete'}
            )
            
            # Step 2: Execute workflow
            self.tasks[task_id]['status'] = 'executing'
            execution_result = await self.executor.execute(workflow)
            
            # Update task status
            if execution_result['status'] == 'completed':
                self.tasks[task_id]['status'] = 'completed'
                self.tasks[task_id]['result'] = execution_result.get('result')
                self.tasks[task_id]['completed_at'] = datetime.utcnow().isoformat()
            else:
                self.tasks[task_id]['status'] = 'failed'
                self.tasks[task_id]['error'] = execution_result.get('error')
                self.tasks[task_id]['failed_at'] = datetime.utcnow().isoformat()
            
            # Save final state
            self.state_store.save_state(
                workflow.workflow_id,
                {
                    'task_id': task_id,
                    'status': self.tasks[task_id]['status'],
                    'result': self.tasks[task_id].get('result')
                }
            )
            
            return {
                'task_id': task_id,
                'status': self.tasks[task_id]['status'],
                'result': self.tasks[task_id].get('result'),
                'workflow_id': workflow.workflow_id
            }
            
        except Exception as e:
            logger.error(
                "Task execution failed",
                task_id=task_id,
                error=str(e),
                exc_info=True
            )
            
            self.tasks[task_id]['status'] = 'failed'
            self.tasks[task_id]['error'] = str(e)
            self.tasks[task_id]['failed_at'] = datetime.utcnow().isoformat()
            
            raise
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get task status
        
        Args:
            task_id: Task ID
            
        Returns:
            Task status dictionary
        """
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self.tasks[task_id].copy()
        
        # Get execution status if workflow is executing
        workflow_id = task.get('workflow_id')
        if workflow_id and task['status'] in ['executing', 'planning']:
            execution_status = self.executor.get_execution_status(workflow_id)
            if execution_status:
                task['execution_status'] = execution_status
        
        return task
    
    def submit_task(self, task: Dict[str, Any]) -> str:
        """
        Submit a task to the queue (async execution)
        
        Args:
            task: Task dictionary
            
        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())
        
        self.task_queue.append({
            'task_id': task_id,
            'task': task,
            'created_at': datetime.utcnow()
        })
        
        logger.info("Task queued", task_id=task_id)
        return task_id
    
    async def process_queue(self):
        """Process tasks in queue"""
        while self.task_queue:
            queued_task = self.task_queue.pop(0)
            task_id = queued_task['task_id']
            task = queued_task['task']
            
            try:
                # Pass task_id to execute to maintain consistency
                await self.execute(task, task_id=task_id)
            except Exception as e:
                logger.error(
                    "Failed to process queued task",
                    task_id=task_id,
                    error=str(e)
                )
    
    def get_queue_size(self) -> int:
        """Get current queue size"""
        return len(self.task_queue)
