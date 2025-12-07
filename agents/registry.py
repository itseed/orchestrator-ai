"""
Agent Registry
Registry for managing agents
"""

from typing import Dict, Any, List, Optional

class AgentRegistry:
    """Registry for managing agents"""
    
    def __init__(self):
        self.agents: Dict[str, Any] = {}
    
    def register(self, agent_id: str, agent: Any, metadata: Dict[str, Any] = None):
        """Register an agent"""
        self.agents[agent_id] = {
            'agent_id': agent_id,
            'agent': agent,
            'metadata': metadata or {},
            'status': 'active',
            'registered_at': None
        }
    
    def unregister(self, agent_id: str):
        """Unregister an agent"""
        if agent_id in self.agents:
            del self.agents[agent_id]
    
    def get(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent by ID"""
        return self.agents.get(agent_id)
    
    def list_agents(self, capability: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all agents, optionally filtered by capability"""
        agents = list(self.agents.values())
        
        if capability:
            agents = [
                a for a in agents 
                if capability in a.get('metadata', {}).get('capabilities', [])
            ]
        
        return agents

