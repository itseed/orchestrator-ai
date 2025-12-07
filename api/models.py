"""
API Models
Pydantic models for API requests and responses
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator, HttpUrl
import re


class TaskRequest(BaseModel):
    """Request model for task submission"""
    type: str = Field(..., description="Task type", min_length=1, max_length=100)
    input: Dict[str, Any] = Field(default_factory=dict, description="Task input data")
    workflow: Optional[str] = Field(None, description="Optional workflow name", max_length=100)
    callback_url: Optional[str] = Field(None, description="Optional webhook callback URL")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional metadata")
    
    @validator('type')
    def validate_task_type(cls, v):
        """Validate task type"""
        if not v or not v.strip():
            raise ValueError("Task type cannot be empty")
        # Allow alphanumeric, underscore, and hyphen
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Task type can only contain alphanumeric characters, underscores, and hyphens")
        return v.strip()
    
    @validator('callback_url')
    def validate_callback_url(cls, v):
        """Validate callback URL if provided"""
        if v:
            # Basic URL validation
            if not (v.startswith('http://') or v.startswith('https://')):
                raise ValueError("Callback URL must start with http:// or https://")
        return v
    
    @validator('input')
    def validate_input(cls, v):
        """Validate input data"""
        if not isinstance(v, dict):
            raise ValueError("Input must be a dictionary")
        # Limit input size (prevent huge payloads)
        import json
        input_size = len(json.dumps(v))
        if input_size > 10 * 1024 * 1024:  # 10MB limit
            raise ValueError("Input data too large (max 10MB)")
        return v


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
