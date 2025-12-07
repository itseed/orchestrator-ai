"""
Base Agent Class
Abstract base class for all AI agents
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
from monitoring import get_logger

logger = get_logger(__name__)


class BaseAgent(ABC):
    """Base class for all AI agents"""
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        capabilities: List[str],
        description: Optional[str] = None,
        version: str = "1.0.0",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize base agent
        
        Args:
            agent_id: Unique identifier for the agent
            name: Human-readable name of the agent
            capabilities: List of capabilities this agent provides
            description: Optional description of the agent
            version: Agent version
            metadata: Optional metadata dictionary
        """
        self.agent_id = agent_id
        self.name = name
        self.capabilities = capabilities or []
        self.description = description
        self.version = version
        self.status = 'inactive'
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow()
        self.last_heartbeat: Optional[datetime] = None
        
        logger.info(
            "Agent initialized",
            agent_id=self.agent_id,
            name=self.name,
            capabilities=self.capabilities
        )
    
    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task
        
        Args:
            task: Task dictionary containing task details
            
        Returns:
            Result dictionary with task execution results
        """
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check agent health
        
        Returns:
            Health status dictionary
        """
        self.last_heartbeat = datetime.utcnow()
        
        return {
            'agent_id': self.agent_id,
            'name': self.name,
            'status': self.status,
            'healthy': self.status == 'active',
            'capabilities': self.capabilities,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'version': self.version
        }
    
    def activate(self):
        """Activate the agent"""
        if self.status != 'active':
            self.status = 'active'
            logger.info("Agent activated", agent_id=self.agent_id)
    
    def deactivate(self):
        """Deactivate the agent"""
        if self.status != 'inactive':
            self.status = 'inactive'
            logger.info("Agent deactivated", agent_id=self.agent_id)
    
    def has_capability(self, capability: str) -> bool:
        """
        Check if agent has a specific capability
        
        Args:
            capability: Capability name to check
            
        Returns:
            True if agent has the capability
        """
        return capability in self.capabilities
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get agent information
        
        Returns:
            Agent information dictionary
        """
        return {
            'agent_id': self.agent_id,
            'name': self.name,
            'description': self.description,
            'capabilities': self.capabilities,
            'status': self.status,
            'version': self.version,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None
        }
    
    async def validate_task(self, task: Dict[str, Any]) -> bool:
        """
        Validate if agent can handle the task
        
        Args:
            task: Task dictionary
            
        Returns:
            True if task is valid for this agent
        """
        # Default implementation - can be overridden
        task_type = task.get('type', '')
        return task_type in self.capabilities or 'generic' in self.capabilities

