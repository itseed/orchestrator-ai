"""
Base Agent Class
Abstract base class for all AI agents
"""

from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAgent(ABC):
    """Base class for all AI agents"""
    
    def __init__(self, agent_id: str, name: str, capabilities: list):
        self.agent_id = agent_id
        self.name = name
        self.capabilities = capabilities
        self.status = 'inactive'
    
    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task"""
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """Check agent health"""
        return {
            'agent_id': self.agent_id,
            'status': self.status,
            'healthy': self.status == 'active'
        }

