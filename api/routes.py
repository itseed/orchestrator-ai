"""
API Routes
Route handlers for orchestrator API
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from monitoring import get_logger
from api.models import TaskRequest, TaskResponse, TaskStatus, ErrorResponse
from orchestrator.engine import OrchestratorEngine
from agents.registry import AgentRegistry
from state.store import StateStore

logger = get_logger(__name__)

# Create router
router = APIRouter(prefix="/api/v1", tags=["orchestrator"])

# Global orchestrator instance (should be initialized in app startup)
_orchestrator: Optional[OrchestratorEngine] = None


def set_orchestrator(orchestrator: OrchestratorEngine):
    """Set orchestrator instance"""
    global _orchestrator
    _orchestrator = orchestrator


def get_orchestrator() -> OrchestratorEngine:
    """Get orchestrator instance"""
    if _orchestrator is None:
        raise HTTPException(
            status_code=500,
            detail="Orchestrator not initialized"
        )
    return _orchestrator


@router.post("/tasks", response_model=TaskResponse, status_code=201)
async def submit_task(
    task: TaskRequest,
    background_tasks: BackgroundTasks
) -> TaskResponse:
    """
    Submit a new task to the orchestrator
    
    Args:
        task: Task request
        background_tasks: FastAPI background tasks
        
    Returns:
        Task response with task_id
    """
    try:
        orchestrator = get_orchestrator()
        
        # Convert to dict
        task_dict = task.dict()
        
        # Submit task asynchronously
        task_id = orchestrator.submit_task(task_dict)
        
        # Execute in background
        background_tasks.add_task(orchestrator.process_queue)
        
        # Estimate completion time (rough estimate)
        estimated_completion = (
            datetime.utcnow() + timedelta(seconds=60)
        ).isoformat()
        
        logger.info("Task submitted via API", task_id=task_id, task_type=task.type)
        
        return TaskResponse(
            task_id=task_id,
            status="pending",
            created_at=datetime.utcnow().isoformat(),
            estimated_completion=estimated_completion
        )
        
    except Exception as e:
        logger.error("Failed to submit task", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str) -> TaskStatus:
    """
    Get task status
    
    Args:
        task_id: Task ID
        
    Returns:
        Task status
    """
    try:
        orchestrator = get_orchestrator()
        status = await orchestrator.get_task_status(task_id)
        
        return TaskStatus(**status)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Failed to get task status", task_id=task_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}/result")
async def get_task_result(task_id: str) -> Dict[str, Any]:
    """
    Get task result
    
    Args:
        task_id: Task ID
        
    Returns:
        Task result
    """
    try:
        orchestrator = get_orchestrator()
        status = await orchestrator.get_task_status(task_id)
        
        if status['status'] != 'completed':
            raise HTTPException(
                status_code=400,
                detail=f"Task not completed. Current status: {status['status']}"
            )
        
        return {
            'task_id': task_id,
            'result': status.get('result'),
            'completed_at': status.get('completed_at')
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get task result", task_id=task_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str) -> Dict[str, Any]:
    """
    Cancel a task
    
    Args:
        task_id: Task ID
        
    Returns:
        Cancellation confirmation
    """
    try:
        orchestrator = get_orchestrator()
        
        # Check if task exists
        status = await orchestrator.get_task_status(task_id)
        
        if status['status'] in ['completed', 'failed']:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel task with status: {status['status']}"
            )
        
        # TODO: Implement task cancellation
        # For now, just return success
        
        logger.info("Task cancellation requested", task_id=task_id)
        
        return {
            'task_id': task_id,
            'status': 'cancellation_requested',
            'message': 'Task cancellation is not yet fully implemented'
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to cancel task", task_id=task_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks")
async def list_tasks(
    status: Optional[str] = None,
    limit: int = 10,
    offset: int = 0
) -> Dict[str, Any]:
    """
    List tasks
    
    Args:
        status: Optional status filter
        limit: Maximum number of results
        offset: Offset for pagination
        
    Returns:
        List of tasks
    """
    try:
        orchestrator = get_orchestrator()
        
        # Get all tasks
        all_tasks = list(orchestrator.tasks.values())
        
        # Filter by status if provided
        if status:
            all_tasks = [t for t in all_tasks if t.get('status') == status]
        
        # Sort by created_at (newest first)
        all_tasks.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        # Paginate
        total = len(all_tasks)
        tasks = all_tasks[offset:offset + limit]
        
        return {
            'tasks': tasks,
            'total': total,
            'limit': limit,
            'offset': offset
        }
        
    except Exception as e:
        logger.error("Failed to list tasks", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Health check endpoints
_health_checker: Optional[Any] = None


def set_health_checker(health_checker: Any):
    """Set health checker instance"""
    global _health_checker
    _health_checker = health_checker


@router.get("/health")
async def get_health() -> Dict[str, Any]:
    """
    Get system health status
    
    Returns:
        System health status
    """
    if _health_checker:
        try:
            return await _health_checker.get_health()
        except Exception as e:
            logger.error("Health check failed", error=str(e))
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    # Basic health check if no health checker configured
    orchestrator = get_orchestrator()
    return {
        'status': 'healthy',
        'message': 'System is operational',
        'timestamp': datetime.utcnow().isoformat()
    }
