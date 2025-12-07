"""
Redis-based State Store
Persistent state store using Redis with versioning and locking
"""

import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import redis.asyncio as aioredis
from monitoring import get_logger
from config.settings import get_settings

logger = get_logger(__name__)


class RedisStateStore:
    """
    Redis-based state store with persistence, versioning, and locking
    
    Features:
    - Persistent state storage in Redis
    - State versioning with history
    - Distributed locking for concurrent access
    - TTL support for state expiration
    """
    
    def __init__(
        self,
        redis_url: Optional[str] = None,
        key_prefix: str = "orchestrator:state:",
        lock_prefix: str = "orchestrator:lock:",
        default_ttl: Optional[int] = None
    ):
        """
        Initialize Redis state store
        
        Args:
            redis_url: Redis connection URL (uses settings if not provided)
            key_prefix: Prefix for state keys
            lock_prefix: Prefix for lock keys
            default_ttl: Default TTL in seconds for state (None = no expiration)
        """
        settings = get_settings()
        self.redis_url = redis_url or settings.redis_url
        self.key_prefix = key_prefix
        self.lock_prefix = lock_prefix
        self.default_ttl = default_ttl
        
        self.redis: Optional[aioredis.Redis] = None
        
        logger.info("RedisStateStore initialized", redis_url=self.redis_url)
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            
            # Test connection
            await self.redis.ping()
            
            logger.info("Connected to Redis for state store")
        except Exception as e:
            logger.error("Failed to connect to Redis", error=str(e))
            raise
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis:
            await self.redis.close()
            self.redis = None
            logger.info("Disconnected from Redis state store")
    
    async def _ensure_connected(self):
        """Ensure Redis connection is active"""
        if not self.redis:
            await self.connect()
        
        try:
            await self.redis.ping()
        except Exception:
            await self.connect()
    
    def _get_state_key(self, workflow_id: str) -> str:
        """Get Redis key for workflow state"""
        return f"{self.key_prefix}{workflow_id}"
    
    def _get_version_key(self, workflow_id: str, version: int) -> str:
        """Get Redis key for specific version"""
        return f"{self.key_prefix}{workflow_id}:v{version}"
    
    def _get_metadata_key(self, workflow_id: str) -> str:
        """Get Redis key for workflow metadata"""
        return f"{self.key_prefix}{workflow_id}:metadata"
    
    def _get_lock_key(self, workflow_id: str) -> str:
        """Get Redis key for lock"""
        return f"{self.lock_prefix}{workflow_id}"
    
    async def save_state(
        self,
        workflow_id: str,
        state: Dict[str, Any],
        version: Optional[int] = None,
        ttl: Optional[int] = None
    ) -> int:
        """
        Save workflow state to Redis
        
        Args:
            workflow_id: Workflow ID
            state: State dictionary
            version: Optional version number (auto-increment if not provided)
            ttl: Optional TTL in seconds (uses default_ttl if not provided)
            
        Returns:
            Version number of saved state
        """
        await self._ensure_connected()
        
        metadata_key = self._get_metadata_key(workflow_id)
        
        # Get current metadata
        metadata_json = await self.redis.get(metadata_key)
        if metadata_json:
            metadata = json.loads(metadata_json)
            current_version = metadata.get('current_version', 0)
        else:
            metadata = {
                'workflow_id': workflow_id,
                'current_version': 0,
                'created_at': datetime.utcnow().isoformat()
            }
            current_version = 0
        
        # Determine version
        if version is None:
            version = current_version + 1
        
        # Save versioned state
        version_key = self._get_version_key(workflow_id, version)
        version_data = {
            'state': state,
            'version': version,
            'created_at': datetime.utcnow().isoformat()
        }
        
        version_ttl = ttl if ttl is not None else self.default_ttl
        if version_ttl:
            await self.redis.setex(
                version_key,
                version_ttl,
                json.dumps(version_data, default=str)
            )
        else:
            await self.redis.set(
                version_key,
                json.dumps(version_data, default=str)
            )
        
        # Update metadata
        metadata['current_version'] = version
        metadata['updated_at'] = datetime.utcnow().isoformat()
        
        metadata_ttl = ttl if ttl is not None else self.default_ttl
        if metadata_ttl:
            await self.redis.setex(
                metadata_key,
                metadata_ttl,
                json.dumps(metadata)
            )
        else:
            await self.redis.set(
                metadata_key,
                json.dumps(metadata)
            )
        
        logger.debug(
            "State saved to Redis",
            workflow_id=workflow_id,
            version=version
        )
        
        return version
    
    async def get_state(
        self,
        workflow_id: str,
        version: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get workflow state from Redis
        
        Args:
            workflow_id: Workflow ID
            version: Optional version number (returns latest if not provided)
            
        Returns:
            State dictionary or None
        """
        await self._ensure_connected()
        
        # Get version number
        if version is None:
            metadata_key = self._get_metadata_key(workflow_id)
            metadata_json = await self.redis.get(metadata_key)
            if not metadata_json:
                return None
            
            metadata = json.loads(metadata_json)
            version = metadata.get('current_version')
        
        if version is None:
            return None
        
        # Get versioned state
        version_key = self._get_version_key(workflow_id, version)
        version_json = await self.redis.get(version_key)
        
        if not version_json:
            return None
        
        version_data = json.loads(version_json)
        return version_data.get('state')
    
    async def get_latest_state(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get latest state for workflow"""
        return await self.get_state(workflow_id)
    
    async def update_state(
        self,
        workflow_id: str,
        updates: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> int:
        """
        Update workflow state (merge updates with current state)
        
        Args:
            workflow_id: Workflow ID
            updates: Dictionary of updates to merge
            ttl: Optional TTL in seconds
            
        Returns:
            New version number
        """
        current_state = await self.get_latest_state(workflow_id) or {}
        
        # Merge updates
        updated_state = {**current_state, **updates}
        
        return await self.save_state(workflow_id, updated_state, ttl=ttl)
    
    async def delete_state(self, workflow_id: str):
        """Delete workflow state from Redis"""
        await self._ensure_connected()
        
        # Get all version keys
        metadata_key = self._get_metadata_key(workflow_id)
        metadata_json = await self.redis.get(metadata_key)
        
        if metadata_json:
            metadata = json.loads(metadata_json)
            current_version = metadata.get('current_version', 0)
            
            # Delete all versions
            keys_to_delete = [metadata_key]
            for version in range(1, current_version + 1):
                version_key = self._get_version_key(workflow_id, version)
                keys_to_delete.append(version_key)
            
            if keys_to_delete:
                await self.redis.delete(*keys_to_delete)
        
        logger.info("State deleted from Redis", workflow_id=workflow_id)
    
    async def list_workflows(self) -> List[str]:
        """List all workflow IDs with saved states"""
        await self._ensure_connected()
        
        # Find all metadata keys
        pattern = f"{self.key_prefix}*:metadata"
        keys = []
        cursor = 0
        
        while True:
            cursor, batch = await self.redis.scan(
                cursor=cursor,
                match=pattern,
                count=100
            )
            keys.extend(batch)
            
            if cursor == 0:
                break
        
        # Extract workflow IDs
        workflow_ids = []
        prefix_len = len(self.key_prefix)
        suffix_len = len(":metadata")
        
        for key in keys:
            workflow_id = key[prefix_len:-suffix_len]
            workflow_ids.append(workflow_id)
        
        return workflow_ids
    
    async def get_state_history(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Get state history for workflow"""
        await self._ensure_connected()
        
        metadata_key = self._get_metadata_key(workflow_id)
        metadata_json = await self.redis.get(metadata_key)
        
        if not metadata_json:
            return []
        
        metadata = json.loads(metadata_json)
        current_version = metadata.get('current_version', 0)
        
        history = []
        for version in range(1, current_version + 1):
            version_key = self._get_version_key(workflow_id, version)
            version_json = await self.redis.get(version_key)
            
            if version_json:
                version_data = json.loads(version_json)
                history.append(version_data)
        
        return sorted(history, key=lambda v: v['version'])
    
    async def acquire_lock(
        self,
        workflow_id: str,
        timeout: int = 10,
        expire: int = 30
    ) -> bool:
        """
        Acquire a distributed lock for workflow state
        
        Args:
            workflow_id: Workflow ID
            timeout: Timeout in seconds to wait for lock
            expire: Lock expiration time in seconds
            
        Returns:
            True if lock acquired, False otherwise
        """
        await self._ensure_connected()
        
        lock_key = self._get_lock_key(workflow_id)
        lock_value = f"{datetime.utcnow().isoformat()}"
        
        # Try to acquire lock with timeout
        start_time = datetime.utcnow()
        
        while True:
            # Try to set lock (NX = only if not exists)
            acquired = await self.redis.set(
                lock_key,
                lock_value,
                ex=expire,
                nx=True
            )
            
            if acquired:
                logger.debug("Lock acquired", workflow_id=workflow_id)
                return True
            
            # Check if timeout exceeded
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            if elapsed >= timeout:
                logger.warning(
                    "Lock acquisition timeout",
                    workflow_id=workflow_id,
                    timeout=timeout
                )
                return False
            
            # Wait before retry
            await asyncio.sleep(0.1)
    
    async def release_lock(self, workflow_id: str) -> bool:
        """
        Release a distributed lock
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            True if lock released, False otherwise
        """
        await self._ensure_connected()
        
        lock_key = self._get_lock_key(workflow_id)
        deleted = await self.redis.delete(lock_key)
        
        if deleted:
            logger.debug("Lock released", workflow_id=workflow_id)
            return True
        
        return False
    
    async def update_state_with_lock(
        self,
        workflow_id: str,
        updates: Dict[str, Any],
        lock_timeout: int = 10,
        lock_expire: int = 30,
        ttl: Optional[int] = None
    ) -> Optional[int]:
        """
        Update state with distributed locking
        
        Args:
            workflow_id: Workflow ID
            updates: Dictionary of updates
            lock_timeout: Lock acquisition timeout
            lock_expire: Lock expiration time
            ttl: Optional TTL for state
            
        Returns:
            New version number or None if lock acquisition failed
        """
        # Acquire lock
        if not await self.acquire_lock(workflow_id, lock_timeout, lock_expire):
            return None
        
        try:
            # Update state
            version = await self.update_state(workflow_id, updates, ttl=ttl)
            return version
        finally:
            # Always release lock
            await self.release_lock(workflow_id)

