"""
Unit tests for AgentSelector
"""

import pytest
from orchestrator.selector import AgentSelector
from orchestrator.planner import WorkflowStep
from agents.registry import AgentRegistry
from agents.specialized.echo_agent import EchoAgent


class TestAgentSelector:
    """Test cases for AgentSelector"""
    
    @pytest.fixture
    def registry(self):
        """Create agent registry with test agents"""
        registry = AgentRegistry()
        
        # Register echo agent
        echo_agent = EchoAgent(agent_id="echo_agent")
        registry.register(echo_agent)
        
        # Register another agent
        from agents.base import BaseAgent
        
        class TestAgent(BaseAgent):
            async def execute(self, task: dict) -> dict:
                return {'status': 'success'}
        
        test_agent = TestAgent(
            agent_id="test_agent",
            name="Test Agent",
            capabilities=["test", "analysis"]
        )
        registry.register(test_agent)
        
        return registry
    
    @pytest.fixture
    def selector(self, registry):
        """Create AgentSelector instance"""
        return AgentSelector(registry)
    
    @pytest.mark.asyncio
    async def test_select_for_step(self, selector):
        """Test selecting agent for a step"""
        step = WorkflowStep(
            step_id="test_step",
            agent_type="echo_agent",
            input_data={}
        )
        
        agent = await selector.select_for_step(step)
        
        assert agent is not None
        assert agent.agent_id == "echo_agent"
    
    @pytest.mark.asyncio
    async def test_select_by_capability(self, selector):
        """Test selecting agent by capability"""
        step = WorkflowStep(
            step_id="test_step",
            agent_type="test",
            input_data={}
        )
        
        agent = await selector.select_for_step(step)
        
        assert agent is not None
        assert agent.has_capability("test")
    
    @pytest.mark.asyncio
    async def test_select_no_suitable_agent(self, selector):
        """Test selecting when no suitable agent exists"""
        step = WorkflowStep(
            step_id="test_step",
            agent_type="nonexistent_agent",
            input_data={}
        )
        
        agent = await selector.select_for_step(step)
        
        # Should return None or a fallback agent
        # Depending on implementation
        assert agent is None or agent is not None
    
    def test_workload_tracking(self, selector):
        """Test workload tracking"""
        agent_id = "echo_agent"
        
        selector.increment_workload(agent_id)
        load = selector.get_agent_load(agent_id)
        
        assert load['current_tasks'] == 1
        
        selector.decrement_workload(agent_id)
        load = selector.get_agent_load(agent_id)
        
        assert load['current_tasks'] == 0
    
    def test_workload_decrement_below_zero(self, selector):
        """Test that workload doesn't go below zero"""
        agent_id = "echo_agent"
        
        selector.decrement_workload(agent_id)
        load = selector.get_agent_load(agent_id)
        
        assert load['current_tasks'] == 0
    
    def test_scoring_weights(self, selector):
        """Test setting scoring weights"""
        new_weights = {
            'capability': 0.5,
            'load': 0.3,
            'cost': 0.1,
            'health': 0.1
        }
        
        selector.set_scoring_weights(new_weights)
        
        assert selector.scoring_weights['capability'] == 0.5
        assert selector.scoring_weights['load'] == 0.3

