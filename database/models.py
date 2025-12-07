"""
SQLAlchemy Database Models
Data models for persistence
"""

from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey, Boolean, Text, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from database.base import Base


class TaskModel(Base):
    """Task model for persistence"""
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    type = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, default="pending", index=True)
    input_data = Column(JSON, nullable=False)
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    estimated_completion = Column(DateTime, nullable=True)
    workflow_id = Column(String, ForeignKey("workflows.id"), nullable=True, index=True)
    
    # Relationship
    workflow = relationship("WorkflowModel", back_populates="tasks")


class WorkflowModel(Base):
    """Workflow model for persistence"""
    __tablename__ = "workflows"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_type = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, default="pending", index=True)
    input_data = Column(JSON, nullable=False)
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    tasks = relationship("TaskModel", back_populates="workflow")
    steps = relationship("WorkflowStepModel", back_populates="workflow", cascade="all, delete-orphan")
    snapshots = relationship("StateSnapshotModel", back_populates="workflow", cascade="all, delete-orphan")


class WorkflowStepModel(Base):
    """Workflow step model for persistence"""
    __tablename__ = "workflow_steps"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id = Column(String, ForeignKey("workflows.id"), nullable=False, index=True)
    step_id = Column(String, nullable=False)
    step_type = Column(String, nullable=False)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=True, index=True)
    status = Column(String, nullable=False, default="pending", index=True)
    input_data = Column(JSON, nullable=True)
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration = Column(Float, nullable=True)  # Duration in seconds
    
    # Relationships
    workflow = relationship("WorkflowModel", back_populates="steps")
    agent = relationship("AgentModel", back_populates="steps")


class AgentModel(Base):
    """Agent model for persistence"""
    __tablename__ = "agents"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    agent_type = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, default="inactive", index=True)
    capabilities = Column(JSON, nullable=False, default=list)
    agent_metadata = Column(JSON, nullable=True)  # Renamed from 'metadata' (SQLAlchemy reserved)
    endpoint = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_heartbeat = Column(DateTime, nullable=True)
    
    # Metrics
    tasks_completed = Column(Integer, default=0, nullable=False)
    tasks_failed = Column(Integer, default=0, nullable=False)
    current_workload = Column(Integer, default=0, nullable=False)
    average_response_time = Column(Float, nullable=True)
    
    # Relationships
    steps = relationship("WorkflowStepModel", back_populates="agent")


class StateSnapshotModel(Base):
    """State snapshot model for persistence"""
    __tablename__ = "state_snapshots"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id = Column(String, ForeignKey("workflows.id"), nullable=False, index=True)
    snapshot_id = Column(String, nullable=False, unique=True, index=True)
    step_id = Column(String, nullable=True)
    state_data = Column(JSON, nullable=False)
    version = Column(Integer, nullable=False)
    snapshot_metadata = Column(JSON, nullable=True)  # Renamed from 'metadata' (SQLAlchemy reserved)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationship
    workflow = relationship("WorkflowModel", back_populates="snapshots")

