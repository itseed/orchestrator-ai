"""
Data Access Layer
Repository pattern for database operations
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from typing import Union
from monitoring import get_logger
from database.models import (
    TaskModel,
    WorkflowModel,
    WorkflowStepModel,
    AgentModel,
    StateSnapshotModel
)

logger = get_logger(__name__)


class TaskRepository:
    """Repository for task operations"""
    
    def __init__(self, session: Union[Session, AsyncSession]):
        """
        Initialize task repository
        
        Args:
            session: Database session (sync or async)
        """
        self.session = session
    
    async def create(self, task_data: Dict[str, Any]) -> TaskModel:
        """Create a new task"""
        task = TaskModel(**task_data)
        self.session.add(task)
        
        if isinstance(self.session, AsyncSession):
            await self.session.commit()
            await self.session.refresh(task)
        else:
            self.session.commit()
            self.session.refresh(task)
        
        logger.debug("Task created", task_id=task.id)
        return task
    
    async def get_by_id(self, task_id: str) -> Optional[TaskModel]:
        """Get task by ID"""
        result = await self.session.execute(
            select(TaskModel).where(TaskModel.id == task_id)
        )
        return result.scalar_one_or_none()
    
    async def update(self, task_id: str, updates: Dict[str, Any]) -> Optional[TaskModel]:
        """Update task"""
        await self.session.execute(
            update(TaskModel)
            .where(TaskModel.id == task_id)
            .values(**updates)
        )
        await self.session.commit()
        return await self.get_by_id(task_id)
    
    async def list(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[TaskModel]:
        """List tasks with optional filters"""
        query = select(TaskModel)
        
        if status:
            query = query.where(TaskModel.status == status)
        
        query = query.order_by(TaskModel.created_at.desc()).limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def delete(self, task_id: str) -> bool:
        """Delete task"""
        result = await self.session.execute(
            delete(TaskModel).where(TaskModel.id == task_id)
        )
        await self.session.commit()
        return result.rowcount > 0


class WorkflowRepository:
    """Repository for workflow operations"""
    
    def __init__(self, session: Session):
        """Initialize workflow repository"""
        self.session = session
    
    async def create(self, workflow_data: Dict[str, Any]) -> WorkflowModel:
        """Create a new workflow"""
        workflow = WorkflowModel(**workflow_data)
        self.session.add(workflow)
        await self.session.commit()
        await self.session.refresh(workflow)
        logger.debug("Workflow created", workflow_id=workflow.id)
        return workflow
    
    async def get_by_id(self, workflow_id: str) -> Optional[WorkflowModel]:
        """Get workflow by ID"""
        result = await self.session.execute(
            select(WorkflowModel).where(WorkflowModel.id == workflow_id)
        )
        return result.scalar_one_or_none()
    
    async def update(self, workflow_id: str, updates: Dict[str, Any]) -> Optional[WorkflowModel]:
        """Update workflow"""
        await self.session.execute(
            update(WorkflowModel)
            .where(WorkflowModel.id == workflow_id)
            .values(**updates)
        )
        await self.session.commit()
        return await self.get_by_id(workflow_id)
    
    async def list(
        self,
        status: Optional[str] = None,
        task_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[WorkflowModel]:
        """List workflows with optional filters"""
        query = select(WorkflowModel)
        
        if status:
            query = query.where(WorkflowModel.status == status)
        
        if task_type:
            query = query.where(WorkflowModel.task_type == task_type)
        
        query = query.order_by(WorkflowModel.created_at.desc()).limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())


class AgentRepository:
    """Repository for agent operations"""
    
    def __init__(self, session: Session):
        """Initialize agent repository"""
        self.session = session
    
    async def create(self, agent_data: Dict[str, Any]) -> AgentModel:
        """Create a new agent"""
        agent = AgentModel(**agent_data)
        self.session.add(agent)
        await self.session.commit()
        await self.session.refresh(agent)
        logger.debug("Agent created", agent_id=agent.id)
        return agent
    
    async def get_by_id(self, agent_id: str) -> Optional[AgentModel]:
        """Get agent by ID"""
        result = await self.session.execute(
            select(AgentModel).where(AgentModel.id == agent_id)
        )
        return result.scalar_one_or_none()
    
    async def update(self, agent_id: str, updates: Dict[str, Any]) -> Optional[AgentModel]:
        """Update agent"""
        updates['updated_at'] = datetime.utcnow()
        await self.session.execute(
            update(AgentModel)
            .where(AgentModel.id == agent_id)
            .values(**updates)
        )
        await self.session.commit()
        return await self.get_by_id(agent_id)
    
    async def list(
        self,
        status: Optional[str] = None,
        agent_type: Optional[str] = None,
        limit: int = 100
    ) -> List[AgentModel]:
        """List agents with optional filters"""
        query = select(AgentModel)
        
        if status:
            query = query.where(AgentModel.status == status)
        
        if agent_type:
            query = query.where(AgentModel.agent_type == agent_type)
        
        query = query.order_by(AgentModel.created_at.desc()).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def update_heartbeat(self, agent_id: str):
        """Update agent heartbeat"""
        await self.session.execute(
            update(AgentModel)
            .where(AgentModel.id == agent_id)
            .values(last_heartbeat=datetime.utcnow())
        )
        await self.session.commit()


class StateSnapshotRepository:
    """Repository for state snapshot operations"""
    
    def __init__(self, session: Session):
        """Initialize state snapshot repository"""
        self.session = session
    
    async def create(self, snapshot_data: Dict[str, Any]) -> StateSnapshotModel:
        """Create a new snapshot"""
        snapshot = StateSnapshotModel(**snapshot_data)
        self.session.add(snapshot)
        await self.session.commit()
        await self.session.refresh(snapshot)
        logger.debug("Snapshot created", snapshot_id=snapshot.id)
        return snapshot
    
    async def get_by_id(self, snapshot_id: str) -> Optional[StateSnapshotModel]:
        """Get snapshot by ID"""
        result = await self.session.execute(
            select(StateSnapshotModel).where(StateSnapshotModel.id == snapshot_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_snapshot_id(self, snapshot_id: str) -> Optional[StateSnapshotModel]:
        """Get snapshot by snapshot_id field"""
        result = await self.session.execute(
            select(StateSnapshotModel).where(StateSnapshotModel.snapshot_id == snapshot_id)
        )
        return result.scalar_one_or_none()
    
    async def list_by_workflow(
        self,
        workflow_id: str,
        limit: int = 100
    ) -> List[StateSnapshotModel]:
        """List snapshots for workflow"""
        result = await self.session.execute(
            select(StateSnapshotModel)
            .where(StateSnapshotModel.workflow_id == workflow_id)
            .order_by(StateSnapshotModel.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_latest(self, workflow_id: str) -> Optional[StateSnapshotModel]:
        """Get latest snapshot for workflow"""
        result = await self.session.execute(
            select(StateSnapshotModel)
            .where(StateSnapshotModel.workflow_id == workflow_id)
            .order_by(StateSnapshotModel.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def delete(self, snapshot_id: str) -> bool:
        """Delete snapshot"""
        result = await self.session.execute(
            delete(StateSnapshotModel).where(StateSnapshotModel.id == snapshot_id)
        )
        await self.session.commit()
        return result.rowcount > 0

