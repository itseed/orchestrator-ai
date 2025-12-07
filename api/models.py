"""
API Models
Pydantic models for API requests and responses
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class TaskRequest(BaseModel):
    """Request model for task submission"""
    type: str = Field(..., description="Task type")
    input: Dict[str, Any] = Field(default_factory=dict, description="Task input data")
    workflow: Optional[str] = Field(None, description="Optional workflow name")
    callback_url: Optional[str] = Field(None, description="Optional webhook callback URL")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional metadata")


class TaskResponse(BaseModel):
    """Response model for task submission"""
    task_id: str
    status: str
    created_at: str
    estimated_completion: Optional[str] = None


class TaskStatus(BaseModel):
    """Task status model"""
    task_id: str
    status: str  # pending, planning, executing, completed, failed
    workflow_id: Optional[str] = None
    progress: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None
    execution_status: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None
    task_id: Optional[str] = None
