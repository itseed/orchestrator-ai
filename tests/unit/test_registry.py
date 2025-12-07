"""
Unit tests for AgentRegistry
"""

import pytest
from agents.registry import AgentRegistry
from agents.specialized.echo_agent import EchoAgent


class TestAgentRegistry:
    """Test cases for AgentRegistry"""
    
    def test_registry_initialization(self):
        """Test registry initialization"""
        registry = AgentRegistry()
        assert registry.count() == 0
    
    def test_register_agent(self):
        """Test agent registration"""
        registry = AgentRegistry()
        agent = EchoAgent(agent_id="test_echo")
        
        result = registry.register(agent)
        
        assert result is True
        assert registry.count() == 1
        assert registry.get("test_echo") == agent
        assert agent.status == "active"
    
    def test_register_agent_inactive(self):
        """Test agent registration without activation"""
        registry = AgentRegistry()
        agent = EchoAgent(agent_id="test_echo")
        
        registry.register(agent, activate=False)
        
        assert agent.status == "inactive"
    
    def test_unregister_agent(self):
        """Test agent unregistration"""
        registry = AgentRegistry()
        agent = EchoAgent(agent_id="test_echo")
        
        registry.register(agent)
        assert registry.count() == 1
        
        result = registry.unregister("test_echo")
        
        assert result is True
        assert registry.count() == 0
        assert agent.status == "inactive"
    
    def test_unregister_nonexistent_agent(self):
        """Test unregistering non-existent agent"""
        registry = AgentRegistry()
        
        result = registry.unregister("nonexistent")
        
        assert result is False
    
    def test_get_agent(self):
        """Test getting agent by ID"""
        registry = AgentRegistry()
        agent = EchoAgent(agent_id="test_echo")
        
        registry.register(agent)
        
        retrieved = registry.get("test_echo")
        assert retrieved == agent
        
        nonexistent = registry.get("nonexistent")
        assert nonexistent is None
    
    def test_list_agents(self):
        """Test listing all agents"""
        registry = AgentRegistry()
        
        agent1 = EchoAgent(agent_id="echo1", name="Echo 1")
        agent2 = EchoAgent(agent_id="echo2", name="Echo 2")
        
        registry.register(agent1)
        registry.register(agent2)
        
        agents = registry.list_agents()
        
        assert len(agents) == 2
        assert any(a['agent_id'] == "echo1" for a in agents)
        assert any(a['agent_id'] == "echo2" for a in agents)
    
    def test_list_agents_by_capability(self):
        """Test listing agents by capability"""
        registry = AgentRegistry()
        
        agent1 = EchoAgent(agent_id="echo1")
        registry.register(agent1)
        
        # Create agent with different capability
        from agents.base import BaseAgent
        
        class TestAgent(BaseAgent):
            async def execute(self, task: dict) -> dict:
                return {}
        
        agent2 = TestAgent(
            agent_id="test_agent",
            name="Test Agent",
            capabilities=["test"]
        )
        registry.register(agent2)
        
        echo_agents = registry.list_agents(capability="echo")
        assert len(echo_agents) == 1
        assert echo_agents[0]['agent_id'] == "echo1"
        
        test_agents = registry.list_agents(capability="test")
        assert len(test_agents) == 1
        assert test_agents[0]['agent_id'] == "test_agent"
    
    def test_find_by_capability(self):
        """Test finding agents by capability"""
        registry = AgentRegistry()
        
        agent1 = EchoAgent(agent_id="echo1")
        agent2 = EchoAgent(agent_id="echo2")
        
        registry.register(agent1)
        registry.register(agent2)
        
        echo_agents = registry.find_by_capability("echo")
        
        assert len(echo_agents) == 2
        assert agent1 in echo_agents
        assert agent2 in echo_agents
    
    def test_get_agent_info(self):
        """Test getting agent information"""
        registry = AgentRegistry()
        agent = EchoAgent(agent_id="test_echo")
        
        registry.register(agent)
        
        info = registry.get_agent_info("test_echo")
        
        assert info is not None
        assert info['agent_id'] == "test_echo"
        assert info['name'] == "Echo Agent"
        assert 'registered_at' in info
        assert 'registry_status' in info
    
    def test_get_stats(self):
        """Test getting registry statistics"""
        registry = AgentRegistry()
        
        agent1 = EchoAgent(agent_id="echo1")
        agent2 = EchoAgent(agent_id="echo2")
        
        registry.register(agent1)
        registry.register(agent2)
        
        stats = registry.get_stats()
        
        assert stats['total_agents'] == 2
        assert stats['active_agents'] == 2
        assert 'echo' in stats['capabilities']

