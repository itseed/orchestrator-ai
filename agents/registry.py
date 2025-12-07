"""
Agent Registry
Registry for managing agents
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from monitoring import get_logger
from agents.base import BaseAgent

logger = get_logger(__name__)


class AgentRegistry:
    """Registry for managing agents"""
    
    def __init__(self):
        """Initialize agent registry"""
        self.agents: Dict[str, Dict[str, Any]] = {}
        logger.info("Agent registry initialized")
    
    def register(
        self,
        agent: BaseAgent,
        metadata: Optional[Dict[str, Any]] = None,
        activate: bool = True
    ) -> bool:
        """
        Register an agent
        
        Args:
            agent: Agent instance to register
            metadata: Optional metadata to attach
            activate: Whether to activate agent after registration
            
        Returns:
            True if registration successful
        """
        if agent.agent_id in self.agents:
            logger.warning(
                "Agent already registered",
                agent_id=agent.agent_id,
                action="overwriting"
            )
        
        # Merge agent metadata with provided metadata
        agent_metadata = agent.metadata.copy()
        if metadata:
            agent_metadata.update(metadata)
        
        self.agents[agent.agent_id] = {
            'agent_id': agent.agent_id,
            'agent': agent,
            'metadata': agent_metadata,
            'status': 'active' if activate else 'inactive',
            'registered_at': datetime.utcnow(),
            'capabilities': agent.capabilities
        }
        
        if activate:
            agent.activate()
        
        logger.info(
            "Agent registered",
            agent_id=agent.agent_id,
            name=agent.name,
            capabilities=agent.capabilities
        )
        
        return True
    
    def unregister(self, agent_id: str) -> bool:
        """
        Unregister an agent
        
        Args:
            agent_id: ID of agent to unregister
            
        Returns:
            True if unregistration successful
        """
        if agent_id not in self.agents:
            logger.warning("Agent not found for unregistration", agent_id=agent_id)
            return False
        
        agent = self.agents[agent_id]['agent']
        if isinstance(agent, BaseAgent):
            agent.deactivate()
        
        del self.agents[agent_id]
        logger.info("Agent unregistered", agent_id=agent_id)
        return True
    
    def get(self, agent_id: str) -> Optional[BaseAgent]:
        """
        Get agent by ID
        
        Args:
            agent_id: ID of agent to retrieve
            
        Returns:
            Agent instance or None if not found
        """
        agent_entry = self.agents.get(agent_id)
        if agent_entry:
            return agent_entry['agent']
        return None
    
    def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get agent information
        
        Args:
            agent_id: ID of agent
            
        Returns:
            Agent information dictionary or None
        """
        agent_entry = self.agents.get(agent_id)
        if not agent_entry:
            return None
        
        agent = agent_entry['agent']
        if isinstance(agent, BaseAgent):
            info = agent.get_info()
            info.update({
                'registered_at': agent_entry['registered_at'].isoformat(),
                'registry_status': agent_entry['status']
            })
            return info
        return agent_entry
    
    def list_agents(
        self,
        capability: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all agents, optionally filtered by capability or status
        
        Args:
            capability: Filter by capability
            status: Filter by status (active, inactive)
            
        Returns:
            List of agent information dictionaries
        """
        agents = []
        
        for agent_entry in self.agents.values():
            agent = agent_entry['agent']
            
            # Filter by capability
            if capability:
                if capability not in agent_entry.get('capabilities', []):
                    if isinstance(agent, BaseAgent):
                        if not agent.has_capability(capability):
                            continue
                    else:
                        continue
            
            # Filter by status
            if status:
                if agent_entry['status'] != status:
                    if isinstance(agent, BaseAgent):
                        if agent.status != status:
                            continue
                    else:
                        continue
            
            # Get agent info
            if isinstance(agent, BaseAgent):
                info = agent.get_info()
                info['registry_status'] = agent_entry['status']
                info['registered_at'] = agent_entry['registered_at'].isoformat()
                agents.append(info)
            else:
                agents.append(agent_entry)
        
        return agents
    
    def find_by_capability(self, capability: str) -> List[BaseAgent]:
        """
        Find agents by capability
        
        Args:
            capability: Capability to search for
            
        Returns:
            List of agent instances with the capability
        """
        matching_agents = []
        
        for agent_entry in self.agents.values():
            agent = agent_entry['agent']
            
            if isinstance(agent, BaseAgent):
                if agent.has_capability(capability):
                    matching_agents.append(agent)
            elif capability in agent_entry.get('capabilities', []):
                matching_agents.append(agent)
        
        return matching_agents
    
    def count(self) -> int:
        """Get total number of registered agents"""
        return len(self.agents)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        stats = {
            'total_agents': len(self.agents),
            'active_agents': 0,
            'inactive_agents': 0,
            'capabilities': set()
        }
        
        for agent_entry in self.agents.values():
            status = agent_entry['status']
            if status == 'active':
                stats['active_agents'] += 1
            else:
                stats['inactive_agents'] += 1
            
            # Collect all capabilities
            agent = agent_entry['agent']
            if isinstance(agent, BaseAgent):
                stats['capabilities'].update(agent.capabilities)
            else:
                stats['capabilities'].update(agent_entry.get('capabilities', []))
        
        stats['capabilities'] = list(stats['capabilities'])
        
        return stats

