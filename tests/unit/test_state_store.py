"""
Unit tests for State Store
"""

import pytest
from state.store import StateStore


class TestStateStore:
    """Test cases for StateStore"""
    
    @pytest.fixture
    def state_store(self):
        """Create StateStore instance"""
        return StateStore()
    
    def test_save_state(self, state_store):
        """Test saving state"""
        workflow_id = "test_workflow"
        state = {"status": "running", "step": 1}
        
        version = state_store.save_state(workflow_id, state)
        
        assert version == 1
        
        retrieved = state_store.get_state(workflow_id)
        assert retrieved == state
    
    def test_save_state_multiple_versions(self, state_store):
        """Test saving multiple state versions"""
        workflow_id = "test_workflow"
        
        state1 = {"status": "step1"}
        state2 = {"status": "step2"}
        state3 = {"status": "step3"}
        
        v1 = state_store.save_state(workflow_id, state1)
        v2 = state_store.save_state(workflow_id, state2)
        v3 = state_store.save_state(workflow_id, state3)
        
        assert v1 == 1
        assert v2 == 2
        assert v3 == 3
        
        # Latest should be v3
        latest = state_store.get_latest_state(workflow_id)
        assert latest == state3
        
        # Get specific version
        v1_state = state_store.get_state(workflow_id, version=1)
        assert v1_state == state1
    
    def test_get_nonexistent_state(self, state_store):
        """Test getting nonexistent state"""
        result = state_store.get_state("nonexistent")
        
        assert result is None
    
    def test_update_state(self, state_store):
        """Test updating state"""
        workflow_id = "test_workflow"
        
        initial_state = {"status": "initial", "value": 10}
        state_store.save_state(workflow_id, initial_state)
        
        updates = {"status": "updated", "value": 20}
        new_version = state_store.update_state(workflow_id, updates)
        
        updated_state = state_store.get_state(workflow_id)
        
        assert updated_state["status"] == "updated"
        assert updated_state["value"] == 20
        assert new_version == 2
    
    def test_delete_state(self, state_store):
        """Test deleting state"""
        workflow_id = "test_workflow"
        state = {"status": "test"}
        
        state_store.save_state(workflow_id, state)
        assert state_store.get_state(workflow_id) is not None
        
        state_store.delete_state(workflow_id)
        assert state_store.get_state(workflow_id) is None
    
    def test_list_workflows(self, state_store):
        """Test listing workflows"""
        state_store.save_state("workflow1", {"status": "test"})
        state_store.save_state("workflow2", {"status": "test"})
        state_store.save_state("workflow3", {"status": "test"})
        
        workflows = state_store.list_workflows()
        
        assert len(workflows) == 3
        assert "workflow1" in workflows
        assert "workflow2" in workflows
        assert "workflow3" in workflows
    
    def test_get_state_history(self, state_store):
        """Test getting state history"""
        workflow_id = "test_workflow"
        
        state_store.save_state(workflow_id, {"step": 1})
        state_store.save_state(workflow_id, {"step": 2})
        state_store.save_state(workflow_id, {"step": 3})
        
        history = state_store.get_state_history(workflow_id)
        
        assert len(history) == 3
        assert history[0]["version"] == 1
        assert history[1]["version"] == 2
        assert history[2]["version"] == 3

