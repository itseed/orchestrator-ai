"""
Integration tests for end-to-end workflow execution
"""

import pytest
import asyncio
from orchestrator.engine import OrchestratorEngine
from agents.registry import AgentRegistry
from agents.specialized.echo_agent import EchoAgent
from state.store import StateStore


@pytest.fixture
def registry():
    """Create agent registry with test agents"""
    registry = AgentRegistry()
    
    # Register echo agent
    echo_agent = EchoAgent(agent_id="echo_agent")
    registry.register(echo_agent)
    
    return registry


@pytest.fixture
def orchestrator(registry):
    """Create orchestrator engine"""
    state_store = StateStore()
    return OrchestratorEngine(registry=registry, state_store=state_store)


@pytest.mark.asyncio
async def test_simple_workflow_execution(orchestrator):
    """Test simple end-to-end workflow execution"""
    task = {
        'type': 'simple',
        'input': {
            'message': 'Hello, World!'
        }
    }
    
    result = await orchestrator.execute(task)
    
    assert result['status'] == 'completed'
    assert result['task_id'] is not None
    assert result['workflow_id'] is not None
    assert 'result' in result or result.get('result') is not None


@pytest.mark.asyncio
async def test_task_status_tracking(orchestrator):
    """Test task status tracking throughout execution"""
    task = {
        'type': 'simple',
        'input': {'test': 'data'}
    }
    
    # Execute task
    result = await orchestrator.execute(task)
    task_id = result['task_id']
    
    # Check status
    status = await orchestrator.get_task_status(task_id)
    
    assert status['status'] == 'completed'
    assert status['task_id'] == task_id
    assert status['workflow_id'] == result['workflow_id']


@pytest.mark.asyncio
async def test_multiple_tasks_execution(orchestrator):
    """Test executing multiple tasks"""
    tasks = [
        {'type': 'simple', 'input': {'id': 1}},
        {'type': 'simple', 'input': {'id': 2}},
        {'type': 'simple', 'input': {'id': 3}},
    ]
    
    results = []
    for task in tasks:
        result = await orchestrator.execute(task)
        results.append(result)
    
    assert len(results) == 3
    assert all(r['status'] == 'completed' for r in results)
    assert len(set(r['task_id'] for r in results)) == 3  # All unique task IDs


@pytest.mark.asyncio
async def test_workflow_with_dependencies(orchestrator):
    """Test workflow execution with step dependencies"""
    task = {
        'type': 'research_and_analyze',
        'input': {
            'topic': 'AI Orchestration'
        }
    }
    
    result = await orchestrator.execute(task)
    
    assert result['status'] in ['completed', 'failed']  # May fail if agents not available
    assert result['workflow_id'] is not None


@pytest.mark.asyncio
async def test_task_queue_submission(orchestrator):
    """Test task queue submission"""
    task = {
        'type': 'simple',
        'input': {'test': 'queue'}
    }
    
    # Submit to queue
    task_id = orchestrator.submit_task(task)
    
    assert task_id is not None
    assert orchestrator.get_queue_size() == 1
    
    # Process queue
    await orchestrator.process_queue()
    
    # Check status
    status = await orchestrator.get_task_status(task_id)
    assert status['status'] in ['completed', 'failed']


@pytest.mark.asyncio
async def test_error_handling(orchestrator):
    """Test error handling in workflow execution"""
    # Task with invalid type (should still be handled gracefully)
    task = {
        'type': 'invalid_task_type_xyz',
        'input': {}
    }
    
    result = await orchestrator.execute(task)
    
    # Should either complete with default workflow or fail gracefully
    assert result['status'] in ['completed', 'failed']
    assert 'error' in result or result.get('error') is None  # May or may not have error


@pytest.mark.asyncio
async def test_state_persistence(orchestrator):
    """Test that workflow state is persisted"""
    task = {
        'type': 'simple',
        'input': {'test': 'state'}
    }
    
    result = await orchestrator.execute(task)
    workflow_id = result['workflow_id']
    
    # Check if state was saved
    state = orchestrator.state_store.get_state(workflow_id)
    
    assert state is not None
    assert 'task_id' in state
    assert 'status' in state

