"""
Integration tests for parallel step execution
"""

import pytest
import asyncio
from orchestrator.engine import OrchestratorEngine
from orchestrator.executor import WorkflowExecutor
from orchestrator.planner import TaskPlanner, WorkflowGraph, WorkflowStep
from agents.registry import AgentRegistry
from agents.specialized.echo_agent import EchoAgent
from orchestrator.selector import AgentSelector
from state.store import StateStore


@pytest.fixture
def registry():
    """Create agent registry"""
    registry = AgentRegistry()
    echo_agent = EchoAgent(agent_id="echo_agent")
    registry.register(echo_agent)
    return registry


@pytest.fixture
def executor(registry):
    """Create workflow executor"""
    selector = AgentSelector(registry)
    return WorkflowExecutor(registry, selector)


@pytest.mark.asyncio
async def test_parallel_steps_execution(executor):
    """Test parallel step execution"""
    # Create workflow with parallel steps
    workflow = WorkflowGraph("test_workflow", "Test", "parallel_test")
    
    # Add parallel steps (no dependencies)
    step1 = WorkflowStep(
        step_id="step1",
        agent_type="echo_agent",
        input_data={"message": "Step 1"}
    )
    step2 = WorkflowStep(
        step_id="step2",
        agent_type="echo_agent",
        input_data={"message": "Step 2"}
    )
    step3 = WorkflowStep(
        step_id="step3",
        agent_type="echo_agent",
        input_data={"message": "Step 3"}
    )
    
    workflow.add_step(step1)
    workflow.add_step(step2)
    workflow.add_step(step3)
    
    # Execute with parallel enabled
    result = await executor.execute(workflow, options={'enable_parallel': True})
    
    assert result['status'] == 'completed'
    assert 'steps' in result
    assert len(result['steps']) == 3


@pytest.mark.asyncio
async def test_sequential_steps_execution(executor):
    """Test sequential step execution"""
    workflow = WorkflowGraph("test_workflow", "Test", "sequential_test")
    
    # Add sequential steps
    step1 = WorkflowStep(
        step_id="step1",
        agent_type="echo_agent",
        input_data={"message": "Step 1"}
    )
    step2 = WorkflowStep(
        step_id="step2",
        agent_type="echo_agent",
        input_data={"message": "Step 2"},
        depends_on=["step1"]
    )
    step3 = WorkflowStep(
        step_id="step3",
        agent_type="echo_agent",
        input_data={"message": "Step 3"},
        depends_on=["step2"]
    )
    
    workflow.add_step(step1)
    workflow.add_step(step2)
    workflow.add_step(step3)
    
    # Execute sequentially
    result = await executor.execute(workflow, options={'enable_parallel': False})
    
    assert result['status'] == 'completed'
    assert 'steps' in result
    assert len(result['steps']) == 3


@pytest.mark.asyncio
async def test_mixed_parallel_sequential(executor):
    """Test workflow with both parallel and sequential steps"""
    workflow = WorkflowGraph("test_workflow", "Test", "mixed_test")
    
    # Parallel group 1
    step1 = WorkflowStep("step1", "echo_agent", {"message": "Step 1"})
    step2 = WorkflowStep("step2", "echo_agent", {"message": "Step 2"})
    
    # Sequential step after parallel group
    step3 = WorkflowStep(
        "step3",
        "echo_agent",
        {"message": "Step 3"},
        depends_on=["step1", "step2"]
    )
    
    workflow.add_step(step1)
    workflow.add_step(step2)
    workflow.add_step(step3)
    
    result = await executor.execute(workflow, options={'enable_parallel': True})
    
    assert result['status'] == 'completed'
    assert 'steps' in result


@pytest.mark.asyncio
async def test_continue_on_error(executor):
    """Test continue_on_error option"""
    workflow = WorkflowGraph("test_workflow", "Test", "error_test")
    
    # Add steps
    step1 = WorkflowStep("step1", "echo_agent", {"message": "Step 1"})
    step2 = WorkflowStep("step2", "nonexistent_agent", {"message": "Step 2"})
    step3 = WorkflowStep("step3", "echo_agent", {"message": "Step 3"})
    
    workflow.add_step(step1)
    workflow.add_step(step2)
    workflow.add_step(step3)
    
    # Execute with continue_on_error
    result = await executor.execute(
        workflow,
        options={'enable_parallel': False, 'continue_on_error': True}
    )
    
    # Should complete with some steps failed
    assert result['status'] in ['completed', 'failed']
    if result['status'] == 'failed':
        assert 'errors' in result


@pytest.mark.asyncio
async def test_parallel_groups_calculation():
    """Test parallel groups calculation"""
    planner = TaskPlanner()
    
    task = {
        'type': 'parallel_analysis',
        'input': {}
    }
    
    workflow = await planner.plan(task)
    parallel_groups = workflow.get_parallel_groups()
    
    assert len(parallel_groups) > 0
    # Check that steps in same group have no dependencies
    for group in parallel_groups:
        if len(group) > 1:
            # Steps in same group should be independent
            for step_id in group:
                step = workflow.get_step(step_id)
                if step:
                    # Should not depend on other steps in same group
                    assert not any(dep in group for dep in step.depends_on if dep != step_id)

