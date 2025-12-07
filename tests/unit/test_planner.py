"""
Unit tests for TaskPlanner
"""

import pytest
from orchestrator.planner import TaskPlanner, WorkflowGraph, WorkflowStep


class TestTaskPlanner:
    """Test cases for TaskPlanner"""
    
    @pytest.fixture
    def planner(self):
        """Create a TaskPlanner instance"""
        return TaskPlanner()
    
    @pytest.mark.asyncio
    async def test_plan_simple_task(self, planner):
        """Test planning a simple task"""
        task = {
            'type': 'simple',
            'input': {'message': 'test'}
        }
        
        workflow = await planner.plan(task)
        
        assert isinstance(workflow, WorkflowGraph)
        assert workflow.task_type == 'simple'
        assert len(workflow.steps) > 0
        assert workflow.workflow_id is not None
    
    @pytest.mark.asyncio
    async def test_plan_research_task(self, planner):
        """Test planning a research task"""
        task = {
            'type': 'research_and_analyze',
            'input': {'topic': 'AI'}
        }
        
        workflow = await planner.plan(task)
        
        assert isinstance(workflow, WorkflowGraph)
        assert workflow.task_type == 'research_and_analyze'
        assert len(workflow.steps) >= 2  # Should have multiple steps
    
    @pytest.mark.asyncio
    async def test_plan_unknown_task(self, planner):
        """Test planning an unknown task type"""
        task = {
            'type': 'unknown_task_type',
            'input': {}
        }
        
        workflow = await planner.plan(task)
        
        assert isinstance(workflow, WorkflowGraph)
        assert len(workflow.steps) > 0  # Should have default step
    
    @pytest.mark.asyncio
    async def test_workflow_execution_order(self, planner):
        """Test workflow execution order calculation"""
        task = {
            'type': 'research_and_analyze',
            'input': {}
        }
        
        workflow = await planner.plan(task)
        execution_order = workflow.calculate_execution_order()
        
        assert len(execution_order) == len(workflow.steps)
        assert len(set(execution_order)) == len(execution_order)  # No duplicates
    
    @pytest.mark.asyncio
    async def test_workflow_parallel_groups(self, planner):
        """Test parallel groups calculation"""
        task = {
            'type': 'parallel_analysis',
            'input': {}
        }
        
        workflow = await planner.plan(task)
        parallel_groups = workflow.get_parallel_groups()
        
        assert len(parallel_groups) > 0
        # Check that steps in same group can run in parallel
        for group in parallel_groups:
            assert len(group) > 0


class TestWorkflowGraph:
    """Test cases for WorkflowGraph"""
    
    def test_workflow_creation(self):
        """Test workflow graph creation"""
        workflow = WorkflowGraph(
            workflow_id="test_workflow",
            name="Test Workflow",
            task_type="test"
        )
        
        assert workflow.workflow_id == "test_workflow"
        assert workflow.name == "Test Workflow"
        assert workflow.task_type == "test"
        assert len(workflow.steps) == 0
    
    def test_add_step(self):
        """Test adding steps to workflow"""
        workflow = WorkflowGraph("test", "Test", "test")
        
        step = WorkflowStep(
            step_id="step1",
            agent_type="test_agent",
            input_data={"test": "data"}
        )
        
        workflow.add_step(step)
        
        assert len(workflow.steps) == 1
        assert workflow.get_step("step1") == step
    
    def test_circular_dependency_detection(self):
        """Test detection of circular dependencies"""
        workflow = WorkflowGraph("test", "Test", "test")
        
        step1 = WorkflowStep("step1", "agent1", depends_on=["step2"])
        step2 = WorkflowStep("step2", "agent2", depends_on=["step1"])
        
        workflow.add_step(step1)
        workflow.add_step(step2)
        
        with pytest.raises(ValueError, match="Circular dependency"):
            workflow.calculate_execution_order()
    
    def test_execution_order_simple(self):
        """Test execution order for simple dependencies"""
        workflow = WorkflowGraph("test", "Test", "test")
        
        step1 = WorkflowStep("step1", "agent1", depends_on=[])
        step2 = WorkflowStep("step2", "agent2", depends_on=["step1"])
        step3 = WorkflowStep("step3", "agent3", depends_on=["step2"])
        
        workflow.add_step(step1)
        workflow.add_step(step2)
        workflow.add_step(step3)
        
        order = workflow.calculate_execution_order()
        
        assert order[0] == "step1"
        assert order[1] == "step2"
        assert order[2] == "step3"

