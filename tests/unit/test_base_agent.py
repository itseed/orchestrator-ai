"""
Unit tests for BaseAgent
"""

import pytest
from datetime import datetime
from agents.base import BaseAgent
from agents.specialized.echo_agent import EchoAgent


class TestAgent(BaseAgent):
    """Test agent implementation"""
    
    async def execute(self, task: dict) -> dict:
        return {'status': 'success', 'result': task}


class TestBaseAgent:
    """Test cases for BaseAgent"""
    
    def test_agent_initialization(self):
        """Test agent initialization"""
        agent = TestAgent(
            agent_id="test_agent",
            name="Test Agent",
            capabilities=["test", "execute"]
        )
        
        assert agent.agent_id == "test_agent"
        assert agent.name == "Test Agent"
        assert "test" in agent.capabilities
        assert agent.status == "inactive"
        assert agent.version == "1.0.0"
    
    def test_agent_activation(self):
        """Test agent activation"""
        agent = TestAgent(
            agent_id="test_agent",
            name="Test Agent",
            capabilities=["test"]
        )
        
        assert agent.status == "inactive"
        agent.activate()
        assert agent.status == "active"
    
    def test_agent_deactivation(self):
        """Test agent deactivation"""
        agent = TestAgent(
            agent_id="test_agent",
            name="Test Agent",
            capabilities=["test"]
        )
        
        agent.activate()
        assert agent.status == "active"
        agent.deactivate()
        assert agent.status == "inactive"
    
    def test_has_capability(self):
        """Test capability checking"""
        agent = TestAgent(
            agent_id="test_agent",
            name="Test Agent",
            capabilities=["test", "execute", "validate"]
        )
        
        assert agent.has_capability("test") is True
        assert agent.has_capability("execute") is True
        assert agent.has_capability("invalid") is False
    
    def test_get_info(self):
        """Test getting agent info"""
        agent = TestAgent(
            agent_id="test_agent",
            name="Test Agent",
            capabilities=["test"],
            description="A test agent"
        )
        
        info = agent.get_info()
        
        assert info['agent_id'] == "test_agent"
        assert info['name'] == "Test Agent"
        assert info['description'] == "A test agent"
        assert info['status'] == "inactive"
        assert 'created_at' in info
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check"""
        agent = TestAgent(
            agent_id="test_agent",
            name="Test Agent",
            capabilities=["test"]
        )
        
        health = await agent.health_check()
        
        assert health['agent_id'] == "test_agent"
        assert health['status'] == "inactive"
        assert health['healthy'] is False
        assert 'last_heartbeat' in health
    
    @pytest.mark.asyncio
    async def test_execute(self):
        """Test task execution"""
        agent = TestAgent(
            agent_id="test_agent",
            name="Test Agent",
            capabilities=["test"]
        )
        
        task = {"type": "test", "data": "test_data"}
        result = await agent.execute(task)
        
        assert result['status'] == 'success'
        assert result['result'] == task
    
    @pytest.mark.asyncio
    async def test_validate_task(self):
        """Test task validation"""
        agent = TestAgent(
            agent_id="test_agent",
            name="Test Agent",
            capabilities=["test", "execute"]
        )
        
        valid_task = {"type": "test"}
        invalid_task = {"type": "unknown"}
        
        # Default validation checks if type is in capabilities
        assert await agent.validate_task(valid_task) is True
        assert await agent.validate_task(invalid_task) is False


class TestEchoAgent:
    """Test cases for EchoAgent"""
    
    @pytest.mark.asyncio
    async def test_echo_execution(self):
        """Test echo agent execution"""
        agent = EchoAgent()
        
        task = {
            "type": "echo",
            "input": {"message": "Hello, World!"}
        }
        
        result = await agent.execute(task)
        
        assert result['status'] == 'success'
        assert result['output'] == task['input']
        assert result['agent_id'] == "echo_agent"

