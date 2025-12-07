"""
Message Protocol
Message format and structure for agent communication
"""

import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator
from monitoring import get_logger

logger = get_logger(__name__)


class MessageType(str, Enum):
    """Message type enumeration"""
    TASK = "task"
    RESPONSE = "response"
    STATUS = "status"
    EVENT = "event"


class Message(BaseModel):
    """
    Base message class for agent communication
    
    Message Format:
    {
        "message_id": "uuid",
        "type": "task|response|status|event",
        "from": "agent_id",
        "to": "agent_id|broadcast",
        "timestamp": "iso_datetime",
        "payload": {},
        "correlation_id": "uuid"
    }
    """
    
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType
    from_agent: str = Field(..., alias="from")
    to_agent: str = Field(..., alias="to")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    payload: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: Optional[str] = None
    
    class Config:
        allow_population_by_field_name = True
        use_enum_values = True
    
    @validator("to_agent")
    def validate_to_agent(cls, v):
        """Validate 'to' field - can be agent_id or 'broadcast'"""
        if v and v.strip():
            return v
        raise ValueError("'to' field cannot be empty")
    
    @validator("from_agent")
    def validate_from_agent(cls, v):
        """Validate 'from' field"""
        if v and v.strip():
            return v
        raise ValueError("'from' field cannot be empty")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return self.dict(by_alias=True, exclude_none=True)
    
    def to_json(self) -> str:
        """Serialize message to JSON string"""
        import json
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create message from dictionary"""
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> "Message":
        """Deserialize message from JSON string"""
        import json
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def is_broadcast(self) -> bool:
        """Check if message is broadcast"""
        return self.to_agent.lower() == "broadcast"
    
    def is_for_agent(self, agent_id: str) -> bool:
        """Check if message is for specific agent"""
        return self.to_agent == agent_id or self.is_broadcast()


class TaskMessage(Message):
    """Task message - work assignment to agent"""
    
    type: MessageType = MessageType.TASK
    
    def __init__(self, **data):
        if "type" not in data:
            data["type"] = MessageType.TASK
        super().__init__(**data)


class ResponseMessage(Message):
    """Response message - result from agent"""
    
    type: MessageType = MessageType.RESPONSE
    
    def __init__(self, **data):
        if "type" not in data:
            data["type"] = MessageType.RESPONSE
        super().__init__(**data)
    
    @validator("correlation_id")
    def validate_correlation_id(cls, v, values):
        """Response should have correlation_id"""
        if not v:
            raise ValueError("Response message must have correlation_id")
        return v


class StatusMessage(Message):
    """Status message - agent status update"""
    
    type: MessageType = MessageType.STATUS
    
    def __init__(self, **data):
        if "type" not in data:
            data["type"] = MessageType.STATUS
        super().__init__(**data)


class EventMessage(Message):
    """Event message - system/agent events"""
    
    type: MessageType = MessageType.EVENT
    event_type: Optional[str] = None
    
    def __init__(self, **data):
        if "type" not in data:
            data["type"] = MessageType.EVENT
        super().__init__(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event message to dictionary with event_type"""
        result = super().to_dict()
        if self.event_type:
            result["event_type"] = self.event_type
        return result


class MessageFactory:
    """Factory for creating message instances"""
    
    @staticmethod
    def create_task_message(
        from_agent: str,
        to_agent: str,
        payload: Dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> TaskMessage:
        """Create task message"""
        return TaskMessage(
            from_agent=from_agent,
            to_agent=to_agent,
            payload=payload,
            correlation_id=correlation_id
        )
    
    @staticmethod
    def create_response_message(
        from_agent: str,
        to_agent: str,
        payload: Dict[str, Any],
        correlation_id: str
    ) -> ResponseMessage:
        """Create response message"""
        return ResponseMessage(
            from_agent=from_agent,
            to_agent=to_agent,
            payload=payload,
            correlation_id=correlation_id
        )
    
    @staticmethod
    def create_status_message(
        from_agent: str,
        to_agent: str,
        payload: Dict[str, Any]
    ) -> StatusMessage:
        """Create status message"""
        return StatusMessage(
            from_agent=from_agent,
            to_agent=to_agent,
            payload=payload
        )
    
    @staticmethod
    def create_event_message(
        from_agent: str,
        event_type: str,
        payload: Dict[str, Any],
        to_agent: str = "broadcast"
    ) -> EventMessage:
        """Create event message"""
        return EventMessage(
            from_agent=from_agent,
            to_agent=to_agent,
            event_type=event_type,
            payload=payload
        )
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> Message:
        """Create message from dictionary based on type"""
        msg_type = data.get("type")
        
        if msg_type == MessageType.TASK:
            return TaskMessage.from_dict(data)
        elif msg_type == MessageType.RESPONSE:
            return ResponseMessage.from_dict(data)
        elif msg_type == MessageType.STATUS:
            return StatusMessage.from_dict(data)
        elif msg_type == MessageType.EVENT:
            return EventMessage.from_dict(data)
        else:
            return Message.from_dict(data)
