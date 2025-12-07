"""
State Store
Manages workflow and agent state
Supports both in-memory and Redis-based storage
"""

import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from monitoring import get_logger

logger = get_logger(__name__)


class StateStore:
    """Base state store for workflows (in-memory implementation)"""
    
    def __init__(self):
        """Initialize state store"""
        self.states: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
        logger.info("StateStore initialized (in-memory)")
    
    def save_state(
        self,
        workflow_id: str,
        state: Dict[str, Any],
        version: Optional[int] = None
    ) -> int:
        """
        Save workflow state (synchronous, thread-safe for single-threaded async)
        
        Note: For true thread-safety in multi-threaded environments,
        use RedisStateStore instead.
        
        Args:
            workflow_id: Workflow ID
            state: State dictionary
            version: Optional version number (auto-increment if not provided)
            
        Returns:
            Version number of saved state
        """
        if workflow_id not in self.states:
            self.states[workflow_id] = {
                'workflow_id': workflow_id,
                'versions': {},
                'current_version': 0,
                'created_at': datetime.utcnow().isoformat()
            }
        
        workflow_states = self.states[workflow_id]
        
        # Auto-increment version
        if version is None:
            version = workflow_states['current_version'] + 1
        
        workflow_states['versions'][version] = {
            'state': state,
            'version': version,
            'created_at': datetime.utcnow().isoformat()
        }
        
        workflow_states['current_version'] = version
        
        logger.debug(
            "State saved",
            workflow_id=workflow_id,
            version=version
        )
        
        return version
    
    async def save_state_async(
        self,
        workflow_id: str,
        state: Dict[str, Any],
        version: Optional[int] = None
    ) -> int:
        """
        Save workflow state (async, thread-safe)
        
        Args:
            workflow_id: Workflow ID
            state: State dictionary
            version: Optional version number (auto-increment if not provided)
            
        Returns:
            Version number of saved state
        """
        async with self._lock:
            if workflow_id not in self.states:
                self.states[workflow_id] = {
                    'workflow_id': workflow_id,
                    'versions': {},
                    'current_version': 0,
                    'created_at': datetime.utcnow().isoformat()
                }
            
            workflow_states = self.states[workflow_id]
            
            # Auto-increment version
            if version is None:
                version = workflow_states['current_version'] + 1
            
            workflow_states['versions'][version] = {
                'state': state,
                'version': version,
                'created_at': datetime.utcnow().isoformat()
            }
            
            workflow_states['current_version'] = version
            
            logger.debug(
                "State saved",
                workflow_id=workflow_id,
                version=version
            )
            
            return version
    
    def get_state(
        self,
        workflow_id: str,
        version: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get workflow state
        
        Args:
            workflow_id: Workflow ID
            version: Optional version number (returns latest if not provided)
            
        Returns:
            State dictionary or None
        """
        if workflow_id not in self.states:
            return None
        
        workflow_states = self.states[workflow_id]
        
        if version is None:
            version = workflow_states['current_version']
        
        state_version = workflow_states['versions'].get(version)
        if state_version:
            return state_version['state']
        
        return None
    
    def get_latest_state(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get latest state for workflow"""
        return self.get_state(workflow_id)
    
    def update_state(
        self,
        workflow_id: str,
        updates: Dict[str, Any]
    ) -> int:
        """
        Update workflow state (merge updates with current state)
        
        Args:
            workflow_id: Workflow ID
            updates: Dictionary of updates to merge
            
        Returns:
            New version number
        """
        current_state = self.get_latest_state(workflow_id) or {}
        
        # Merge updates
        updated_state = {**current_state, **updates}
        
        return self.save_state(workflow_id, updated_state)
    
    def delete_state(self, workflow_id: str):
        """Delete workflow state"""
        if workflow_id in self.states:
            del self.states[workflow_id]
            logger.info("State deleted", workflow_id=workflow_id)
    
    def list_workflows(self) -> List[str]:
        """List all workflow IDs with saved states"""
        return list(self.states.keys())
    
    def get_state_history(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Get state history for workflow"""
        if workflow_id not in self.states:
            return []
        
        workflow_states = self.states[workflow_id]
        versions = workflow_states['versions']
        
        return sorted(
            list(versions.values()),
            key=lambda v: v['version']
        )
