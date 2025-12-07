"""
Echo Agent
Simple agent that echoes back the input (for testing)
"""

from typing import Dict, Any
from agents.base import BaseAgent
from monitoring import get_logger

logger = get_logger(__name__)


class EchoAgent(BaseAgent):
    """Simple echo agent for testing purposes"""
    
    def __init__(self, agent_id: str = "echo_agent", name: str = "Echo Agent"):
        super().__init__(
            agent_id=agent_id,
            name=name,
            capabilities=["echo", "test", "generic"],
            description="Simple agent that echoes back the input",
            version="1.0.0"
        )
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute echo task - returns input as output
        
        Args:
            task: Task dictionary with input data
            
        Returns:
            Result dictionary with echoed data
        """
        logger.info("Echo agent executing task", agent_id=self.agent_id)
        
        input_data = task.get('input', task)
        
        result = {
            'status': 'success',
            'agent_id': self.agent_id,
            'agent_name': self.name,
            'input': input_data,
            'output': input_data,
            'message': 'Echoed successfully'
        }
        
        logger.info("Echo agent task completed", agent_id=self.agent_id)
        return result

