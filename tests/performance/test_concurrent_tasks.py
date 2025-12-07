"""
Performance tests for concurrent task handling
"""

import pytest
import asyncio
import time
from orchestrator.engine import OrchestratorEngine
from agents.registry import AgentRegistry
from agents.specialized.echo_agent import EchoAgent
from state.store import StateStore


@pytest.fixture
def orchestrator():
    """Create orchestrator engine"""
    registry = AgentRegistry()
    echo_agent = EchoAgent(agent_id="echo_agent")
    registry.register(echo_agent)
    state_store = StateStore()
    return OrchestratorEngine(registry=registry, state_store=state_store)


@pytest.mark.asyncio
async def test_concurrent_task_execution(orchestrator):
    """Test concurrent task execution performance"""
    num_tasks = 10
    tasks = [
        {'type': 'simple', 'input': {'id': i, 'message': f'Task {i}'}}
        for i in range(num_tasks)
    ]
    
    start_time = time.time()
    
    # Execute all tasks concurrently
    results = await asyncio.gather(*[
        orchestrator.execute(task) for task in tasks
    ])
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # Verify all tasks completed
    assert len(results) == num_tasks
    assert all(r['status'] == 'completed' for r in results)
    
    # Performance assertion: should complete in reasonable time
    # (10 tasks should complete in less than 5 seconds)
    assert execution_time < 5.0, f"Execution took {execution_time:.2f}s, expected < 5.0s"
    
    print(f"\n✅ Executed {num_tasks} concurrent tasks in {execution_time:.2f}s")
    print(f"   Average: {execution_time/num_tasks:.3f}s per task")


@pytest.mark.asyncio
async def test_sequential_vs_parallel_performance(orchestrator):
    """Compare sequential vs parallel execution performance"""
    num_tasks = 5
    tasks = [
        {'type': 'simple', 'input': {'id': i}}
        for i in range(num_tasks)
    ]
    
    # Sequential execution
    start_time = time.time()
    sequential_results = []
    for task in tasks:
        result = await orchestrator.execute(task)
        sequential_results.append(result)
    sequential_time = time.time() - start_time
    
    # Parallel execution
    start_time = time.time()
    parallel_results = await asyncio.gather(*[
        orchestrator.execute(task) for task in tasks
    ])
    parallel_time = time.time() - start_time
    
    # Parallel should be faster (or at least not significantly slower)
    print(f"\n📊 Performance Comparison:")
    print(f"   Sequential: {sequential_time:.3f}s")
    print(f"   Parallel:   {parallel_time:.3f}s")
    print(f"   Speedup:    {sequential_time/parallel_time:.2f}x")
    
    assert len(sequential_results) == len(parallel_results) == num_tasks


@pytest.mark.asyncio
async def test_memory_usage_under_load(orchestrator):
    """Test memory usage with multiple tasks"""
    import sys
    
    num_tasks = 20
    tasks = [
        {'type': 'simple', 'input': {'id': i, 'data': 'x' * 1000}}
        for i in range(num_tasks)
    ]
    
    # Execute tasks
    results = await asyncio.gather(*[
        orchestrator.execute(task) for task in tasks
    ])
    
    # Check that all completed
    assert len(results) == num_tasks
    assert all(r['status'] == 'completed' for r in results)
    
    # Memory check: orchestrator should not have excessive memory usage
    # (This is a basic check - for detailed profiling, use memory_profiler)
    task_count = len(orchestrator.tasks)
    queue_size = orchestrator.get_queue_size()
    
    print(f"\n💾 Memory Usage Check:")
    print(f"   Tasks in memory: {task_count}")
    print(f"   Queue size: {queue_size}")
    
    # Should not have excessive tasks in memory
    assert task_count <= num_tasks * 2  # Allow some overhead


@pytest.mark.asyncio
async def test_response_time_consistency(orchestrator):
    """Test response time consistency across multiple requests"""
    num_requests = 10
    response_times = []
    
    for i in range(num_requests):
        task = {'type': 'simple', 'input': {'id': i}}
        
        start_time = time.time()
        result = await orchestrator.execute(task)
        end_time = time.time()
        
        response_times.append(end_time - start_time)
        assert result['status'] == 'completed'
    
    avg_time = sum(response_times) / len(response_times)
    min_time = min(response_times)
    max_time = max(response_times)
    
    print(f"\n⏱️  Response Time Statistics:")
    print(f"   Average: {avg_time:.3f}s")
    print(f"   Min:     {min_time:.3f}s")
    print(f"   Max:     {max_time:.3f}s")
    print(f"   Range:   {max_time - min_time:.3f}s")
    
    # Response times should be relatively consistent
    # (max should not be more than 3x the min for simple tasks)
    if min_time > 0:
        assert max_time / min_time < 3.0, "Response times too inconsistent"


@pytest.mark.asyncio
async def test_queue_processing_performance(orchestrator):
    """Test queue processing performance"""
    num_tasks = 15
    
    # Submit all tasks to queue
    task_ids = []
    for i in range(num_tasks):
        task = {'type': 'simple', 'input': {'id': i}}
        task_id = orchestrator.submit_task(task)
        task_ids.append(task_id)
    
    assert orchestrator.get_queue_size() == num_tasks
    
    # Process queue
    start_time = time.time()
    await orchestrator.process_queue()
    processing_time = time.time() - start_time
    
    # Verify all tasks processed
    for task_id in task_ids:
        status = await orchestrator.get_task_status(task_id)
        assert status['status'] in ['completed', 'failed']
    
    print(f"\n📬 Queue Processing:")
    print(f"   Processed {num_tasks} tasks in {processing_time:.2f}s")
    print(f"   Rate: {num_tasks/processing_time:.1f} tasks/sec")
    
    assert processing_time < 10.0  # Should process in reasonable time

