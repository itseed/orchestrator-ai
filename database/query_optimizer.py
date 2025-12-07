"""
Query Optimization
Optimized database queries and indexing strategies
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, Index
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from monitoring import get_logger
from database.models import TaskModel, WorkflowModel, WorkflowStepModel, AgentModel

logger = get_logger(__name__)


class QueryOptimizer:
    """Query optimizer for database operations"""
    
    @staticmethod
    def optimize_task_query(
        query,
        include_workflow: bool = False,
        include_steps: bool = False
    ):
        """
        Optimize task query with eager loading
        
        Args:
            query: SQLAlchemy query
            include_workflow: Whether to eagerly load workflow
            include_steps: Whether to eagerly load steps
            
        Returns:
            Optimized query
        """
        if include_workflow:
            query = query.options(selectinload(TaskModel.workflow))
        
        return query
    
    @staticmethod
    def optimize_workflow_query(
        query,
        include_tasks: bool = False,
        include_steps: bool = False,
        include_snapshots: bool = False
    ):
        """
        Optimize workflow query with eager loading
        
        Args:
            query: SQLAlchemy query
            include_tasks: Whether to eagerly load tasks
            include_steps: Whether to eagerly load steps
            include_snapshots: Whether to eagerly load snapshots
            
        Returns:
            Optimized query
        """
        options = []
        
        if include_tasks:
            options.append(selectinload(WorkflowModel.tasks))
        
        if include_steps:
            options.append(selectinload(WorkflowModel.steps))
        
        if include_snapshots:
            options.append(selectinload(WorkflowModel.snapshots))
        
        if options:
            query = query.options(*options)
        
        return query
    
    @staticmethod
    def optimize_agent_query(
        query,
        include_steps: bool = False
    ):
        """
        Optimize agent query with eager loading
        
        Args:
            query: SQLAlchemy query
            include_steps: Whether to eagerly load steps
            
        Returns:
            Optimized query
        """
        if include_steps:
            query = query.options(selectinload(AgentModel.steps))
        
        return query
    
    @staticmethod
    async def get_task_statistics(
        session: AsyncSession,
        workflow_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get task statistics with optimized query
        
        Args:
            session: Database session
            workflow_id: Optional workflow ID filter
            
        Returns:
            Task statistics dictionary
        """
        query = select(
            func.count(TaskModel.id).label('total'),
            func.count(TaskModel.id).filter(TaskModel.status == 'completed').label('completed'),
            func.count(TaskModel.id).filter(TaskModel.status == 'failed').label('failed'),
            func.count(TaskModel.id).filter(TaskModel.status == 'pending').label('pending'),
            func.count(TaskModel.id).filter(TaskModel.status == 'running').label('running')
        )
        
        if workflow_id:
            query = query.filter(TaskModel.workflow_id == workflow_id)
        
        result = await session.execute(query)
        row = result.first()
        
        return {
            'total': row.total or 0,
            'completed': row.completed or 0,
            'failed': row.failed or 0,
            'pending': row.pending or 0,
            'running': row.running or 0
        }
    
    @staticmethod
    async def get_workflow_statistics(
        session: AsyncSession,
        task_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get workflow statistics with optimized query
        
        Args:
            session: Database session
            task_type: Optional task type filter
            
        Returns:
            Workflow statistics dictionary
        """
        query = select(
            func.count(WorkflowModel.id).label('total'),
            func.count(WorkflowModel.id).filter(WorkflowModel.status == 'completed').label('completed'),
            func.count(WorkflowModel.id).filter(WorkflowModel.status == 'failed').label('failed'),
            func.count(WorkflowModel.id).filter(WorkflowModel.status == 'pending').label('pending'),
            func.count(WorkflowModel.id).filter(WorkflowModel.status == 'running').label('running')
        )
        
        if task_type:
            query = query.filter(WorkflowModel.task_type == task_type)
        
        result = await session.execute(query)
        row = result.first()
        
        return {
            'total': row.total or 0,
            'completed': row.completed or 0,
            'failed': row.failed or 0,
            'pending': row.pending or 0,
            'running': row.running or 0
        }


def create_indexes():
    """
    Create database indexes for query optimization
    
    This should be called during database initialization
    """
    from database.base import Base
    from database.models import TaskModel, WorkflowModel, WorkflowStepModel, AgentModel
    
    indexes = [
        # Composite indexes for common queries
        Index('idx_task_status_created', TaskModel.status, TaskModel.created_at),
        Index('idx_workflow_status_created', WorkflowModel.status, WorkflowModel.created_at),
        Index('idx_workflow_task_type_status', WorkflowModel.task_type, WorkflowModel.status),
        Index('idx_step_status_workflow', WorkflowStepModel.status, WorkflowStepModel.workflow_id),
        Index('idx_agent_status_type', AgentModel.status, AgentModel.agent_type),
    ]
    
    logger.info("Database indexes created", count=len(indexes))
    return indexes

