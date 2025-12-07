"""
State Snapshots
Checkpoint and recovery mechanisms for workflow state
"""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from monitoring import get_logger
from state.store import StateStore
from state.redis_store import RedisStateStore

logger = get_logger(__name__)


class StateSnapshot:
    """
    State snapshot manager for checkpoint creation and recovery
    
    Features:
    - Checkpoint creation at specific workflow states
    - Restore workflow from checkpoint
    - Snapshot metadata and versioning
    - Recovery automation
    """
    
    def __init__(self, state_store: Optional[StateStore] = None):
        """
        Initialize state snapshot manager
        
        Args:
            state_store: StateStore instance (uses in-memory if not provided)
        """
        self.state_store = state_store or StateStore()
        self.snapshots: Dict[str, Dict[str, Any]] = {}
        logger.info("StateSnapshot initialized")
    
    def create_checkpoint(
        self,
        workflow_id: str,
        checkpoint_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a checkpoint for workflow state
        
        Args:
            workflow_id: Workflow ID
            checkpoint_name: Optional checkpoint name (auto-generated if not provided)
            metadata: Optional metadata to store with checkpoint
            
        Returns:
            Checkpoint ID
        """
        import uuid
        
        # Get current state
        current_state = self.state_store.get_latest_state(workflow_id)
        if not current_state:
            raise ValueError(f"No state found for workflow {workflow_id}")
        
        # Get state history for context
        state_history = self.state_store.get_state_history(workflow_id)
        current_version = len(state_history)
        
        # Generate checkpoint ID
        checkpoint_id = checkpoint_name or f"checkpoint_{uuid.uuid4().hex[:8]}"
        full_checkpoint_id = f"{workflow_id}:{checkpoint_id}"
        
        # Create snapshot
        snapshot = {
            'checkpoint_id': full_checkpoint_id,
            'workflow_id': workflow_id,
            'checkpoint_name': checkpoint_name or checkpoint_id,
            'state': current_state,
            'state_version': current_version,
            'state_history': state_history,
            'metadata': metadata or {},
            'created_at': datetime.utcnow().isoformat()
        }
        
        self.snapshots[full_checkpoint_id] = snapshot
        
        logger.info(
            "Checkpoint created",
            checkpoint_id=full_checkpoint_id,
            workflow_id=workflow_id,
            state_version=current_version
        )
        
        return full_checkpoint_id
    
    def get_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """
        Get checkpoint by ID
        
        Args:
            checkpoint_id: Full checkpoint ID (workflow_id:checkpoint_name)
            
        Returns:
            Checkpoint snapshot or None
        """
        return self.snapshots.get(checkpoint_id)
    
    def list_checkpoints(self, workflow_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all checkpoints
        
        Args:
            workflow_id: Optional workflow ID to filter checkpoints
            
        Returns:
            List of checkpoint metadata
        """
        if workflow_id:
            checkpoints = [
                snapshot for checkpoint_id, snapshot in self.snapshots.items()
                if snapshot['workflow_id'] == workflow_id
            ]
        else:
            checkpoints = list(self.snapshots.values())
        
        # Sort by creation time (newest first)
        return sorted(
            checkpoints,
            key=lambda c: c['created_at'],
            reverse=True
        )
    
    def restore_from_checkpoint(
        self,
        checkpoint_id: str,
        restore_state: bool = True
    ) -> Dict[str, Any]:
        """
        Restore workflow state from checkpoint
        
        Args:
            checkpoint_id: Full checkpoint ID
            restore_state: Whether to restore the actual state (True) or just return snapshot (False)
            
        Returns:
            Restored state or snapshot data
        """
        snapshot = self.get_checkpoint(checkpoint_id)
        if not snapshot:
            raise ValueError(f"Checkpoint not found: {checkpoint_id}")
        
        workflow_id = snapshot['workflow_id']
        
        logger.info(
            "Restoring from checkpoint",
            checkpoint_id=checkpoint_id,
            workflow_id=workflow_id,
            restore_state=restore_state
        )
        
        if restore_state:
            # Restore state to state store
            restored_state = snapshot['state']
            self.state_store.save_state(
                workflow_id,
                restored_state,
                version=snapshot['state_version']
            )
            
            logger.info(
                "State restored from checkpoint",
                checkpoint_id=checkpoint_id,
                workflow_id=workflow_id
            )
            
            return restored_state
        
        return snapshot
    
    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """
        Delete a checkpoint
        
        Args:
            checkpoint_id: Full checkpoint ID
            
        Returns:
            True if deleted, False if not found
        """
        if checkpoint_id in self.snapshots:
            del self.snapshots[checkpoint_id]
            logger.info("Checkpoint deleted", checkpoint_id=checkpoint_id)
            return True
        
        return False
    
    def cleanup_old_checkpoints(
        self,
        workflow_id: Optional[str] = None,
        keep_count: int = 10,
        older_than_days: Optional[int] = None
    ) -> int:
        """
        Cleanup old checkpoints
        
        Args:
            workflow_id: Optional workflow ID to filter
            keep_count: Number of recent checkpoints to keep
            older_than_days: Delete checkpoints older than this many days
            
        Returns:
            Number of checkpoints deleted
        """
        checkpoints = self.list_checkpoints(workflow_id)
        
        if not checkpoints:
            return 0
        
        deleted_count = 0
        
        # Filter by age if specified
        if older_than_days:
            cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
            old_checkpoints = [
                c for c in checkpoints
                if datetime.fromisoformat(c['created_at']) < cutoff_date
            ]
            
            for checkpoint in old_checkpoints:
                if self.delete_checkpoint(checkpoint['checkpoint_id']):
                    deleted_count += 1
        
        # Keep only recent N checkpoints
        if len(checkpoints) > keep_count:
            # Sort by creation time (oldest first for deletion)
            sorted_checkpoints = sorted(
                checkpoints,
                key=lambda c: c['created_at']
            )
            
            # Delete oldest checkpoints beyond keep_count
            to_delete = sorted_checkpoints[:-keep_count]
            
            for checkpoint in to_delete:
                if self.delete_checkpoint(checkpoint['checkpoint_id']):
                    deleted_count += 1
        
        logger.info(
            "Checkpoint cleanup completed",
            deleted_count=deleted_count,
            workflow_id=workflow_id
        )
        
        return deleted_count


class RedisStateSnapshot:
    """
    Redis-based state snapshot manager for distributed environments
    """
    
    def __init__(self, redis_state_store: RedisStateStore):
        """
        Initialize Redis-based snapshot manager
        
        Args:
            redis_state_store: RedisStateStore instance
        """
        self.state_store = redis_state_store
        self.snapshot_prefix = "orchestrator:snapshot:"
        logger.info("RedisStateSnapshot initialized")
    
    def _get_snapshot_key(self, checkpoint_id: str) -> str:
        """Get Redis key for snapshot"""
        return f"{self.snapshot_prefix}{checkpoint_id}"
    
    def _get_workflow_snapshots_key(self, workflow_id: str) -> str:
        """Get Redis key for workflow snapshot list"""
        return f"{self.snapshot_prefix}workflow:{workflow_id}"
    
    async def create_checkpoint(
        self,
        workflow_id: str,
        checkpoint_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None
    ) -> str:
        """
        Create a checkpoint for workflow state in Redis
        
        Args:
            workflow_id: Workflow ID
            checkpoint_name: Optional checkpoint name
            metadata: Optional metadata
            ttl: Optional TTL in seconds
            
        Returns:
            Checkpoint ID
        """
        import uuid
        
        await self.state_store._ensure_connected()
        
        # Get current state
        current_state = await self.state_store.get_latest_state(workflow_id)
        if not current_state:
            raise ValueError(f"No state found for workflow {workflow_id}")
        
        # Get state history
        state_history = await self.state_store.get_state_history(workflow_id)
        current_version = len(state_history)
        
        # Generate checkpoint ID
        checkpoint_id = checkpoint_name or f"checkpoint_{uuid.uuid4().hex[:8]}"
        full_checkpoint_id = f"{workflow_id}:{checkpoint_id}"
        
        # Create snapshot
        snapshot = {
            'checkpoint_id': full_checkpoint_id,
            'workflow_id': workflow_id,
            'checkpoint_name': checkpoint_name or checkpoint_id,
            'state': current_state,
            'state_version': current_version,
            'metadata': metadata or {},
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Save snapshot to Redis
        snapshot_key = self._get_snapshot_key(full_checkpoint_id)
        snapshot_json = json.dumps(snapshot, default=str)
        
        if ttl:
            await self.state_store.redis.setex(snapshot_key, ttl, snapshot_json)
        else:
            await self.state_store.redis.set(snapshot_key, snapshot_json)
        
        # Add to workflow snapshot list
        workflow_snapshots_key = self._get_workflow_snapshots_key(workflow_id)
        await self.state_store.redis.sadd(workflow_snapshots_key, full_checkpoint_id)
        
        logger.info(
            "Checkpoint created in Redis",
            checkpoint_id=full_checkpoint_id,
            workflow_id=workflow_id
        )
        
        return full_checkpoint_id
    
    async def get_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """Get checkpoint from Redis"""
        await self.state_store._ensure_connected()
        
        snapshot_key = self._get_snapshot_key(checkpoint_id)
        snapshot_json = await self.state_store.redis.get(snapshot_key)
        
        if not snapshot_json:
            return None
        
        return json.loads(snapshot_json)
    
    async def restore_from_checkpoint(
        self,
        checkpoint_id: str,
        restore_state: bool = True
    ) -> Dict[str, Any]:
        """Restore workflow state from Redis checkpoint"""
        snapshot = await self.get_checkpoint(checkpoint_id)
        if not snapshot:
            raise ValueError(f"Checkpoint not found: {checkpoint_id}")
        
        workflow_id = snapshot['workflow_id']
        
        if restore_state:
            restored_state = snapshot['state']
            await self.state_store.save_state(
                workflow_id,
                restored_state,
                version=snapshot['state_version']
            )
            
            logger.info(
                "State restored from Redis checkpoint",
                checkpoint_id=checkpoint_id,
                workflow_id=workflow_id
            )
            
            return restored_state
        
        return snapshot
    
    async def list_checkpoints(self, workflow_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List checkpoints from Redis"""
        await self.state_store._ensure_connected()
        
        if workflow_id:
            workflow_snapshots_key = self._get_workflow_snapshots_key(workflow_id)
            checkpoint_ids = await self.state_store.redis.smembers(workflow_snapshots_key)
        else:
            # Find all snapshot keys
            pattern = f"{self.snapshot_prefix}*"
            checkpoint_ids = set()
            cursor = 0
            
            while True:
                cursor, batch = await self.state_store.redis.scan(
                    cursor=cursor,
                    match=pattern,
                    count=100
                )
                
                # Filter out workflow list keys
                for key in batch:
                    if not key.startswith(f"{self.snapshot_prefix}workflow:"):
                        checkpoint_id = key[len(self.snapshot_prefix):]
                        checkpoint_ids.add(checkpoint_id)
                
                if cursor == 0:
                    break
        
        # Load snapshot data
        checkpoints = []
        for checkpoint_id in checkpoint_ids:
            snapshot = await self.get_checkpoint(checkpoint_id)
            if snapshot:
                checkpoints.append(snapshot)
        
        return sorted(checkpoints, key=lambda c: c['created_at'], reverse=True)
