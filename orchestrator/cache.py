"""
Caching Strategy
Result caching with invalidation policies
"""

from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import json
from monitoring import get_logger

logger = get_logger(__name__)


class CachePolicy(str, Enum):
    """Cache invalidation policies"""
    TTL = "ttl"  # Time-to-live
    EVENT_BASED = "event_based"  # Invalidate on events
    LRU = "lru"  # Least recently used
    MANUAL = "manual"  # Manual invalidation only


class CacheEntry:
    """Cache entry with metadata"""
    
    def __init__(
        self,
        key: str,
        value: Any,
        ttl: Optional[float] = None,
        created_at: Optional[datetime] = None
    ):
        """
        Initialize cache entry
        
        Args:
            key: Cache key
            value: Cached value
            ttl: Time-to-live in seconds
            created_at: Creation timestamp
        """
        self.key = key
        self.value = value
        self.ttl = ttl
        self.created_at = created_at or datetime.utcnow()
        self.last_accessed = datetime.utcnow()
        self.access_count = 0
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        if self.ttl is None:
            return False
        
        elapsed = (datetime.utcnow() - self.created_at).total_seconds()
        return elapsed > self.ttl
    
    def access(self):
        """Record access to cache entry"""
        self.last_accessed = datetime.utcnow()
        self.access_count += 1


class CacheManager:
    """
    Cache manager with multiple invalidation policies
    
    Features:
    - TTL-based expiration
    - Event-based invalidation
    - LRU eviction
    - Manual invalidation
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: Optional[float] = None,
        policy: CachePolicy = CachePolicy.TTL
    ):
        """
        Initialize cache manager
        
        Args:
            max_size: Maximum number of cache entries
            default_ttl: Default TTL in seconds
            policy: Cache invalidation policy
        """
        self.cache: Dict[str, CacheEntry] = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.policy = policy
        logger.info(
            "CacheManager initialized",
            max_size=max_size,
            default_ttl=default_ttl,
            policy=policy
        )
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Generate cache key from arguments
        
        Args:
            prefix: Key prefix
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Cache key string
        """
        # Serialize arguments
        key_data = {
            'prefix': prefix,
            'args': args,
            'kwargs': kwargs
        }
        
        key_json = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_json.encode()).hexdigest()
        
        return f"{prefix}:{key_hash}"
    
    def get(
        self,
        key: str,
        default: Optional[Any] = None
    ) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            default: Default value if not found
            
        Returns:
            Cached value or default
        """
        entry = self.cache.get(key)
        
        if entry is None:
            return default
        
        # Check if expired
        if entry.is_expired():
            logger.debug("Cache entry expired", key=key)
            del self.cache[key]
            return default
        
        # Record access
        entry.access()
        
        logger.debug("Cache hit", key=key)
        return entry.value
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[float] = None
    ):
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional TTL in seconds (uses default_ttl if not provided)
        """
        # Check if cache is full
        if len(self.cache) >= self.max_size:
            self._evict_entries()
        
        ttl = ttl if ttl is not None else self.default_ttl
        
        entry = CacheEntry(key=key, value=value, ttl=ttl)
        self.cache[key] = entry
        
        logger.debug("Cache entry created", key=key, ttl=ttl)
    
    def delete(self, key: str) -> bool:
        """
        Delete cache entry
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted, False if not found
        """
        if key in self.cache:
            del self.cache[key]
            logger.debug("Cache entry deleted", key=key)
            return True
        return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate cache entries matching pattern
        
        Args:
            pattern: Key pattern (prefix matching)
            
        Returns:
            Number of entries invalidated
        """
        keys_to_delete = [
            key for key in self.cache.keys()
            if key.startswith(pattern)
        ]
        
        for key in keys_to_delete:
            del self.cache[key]
        
        logger.info(
            "Cache entries invalidated",
            pattern=pattern,
            count=len(keys_to_delete)
        )
        
        return len(keys_to_delete)
    
    def clear(self):
        """Clear all cache entries"""
        count = len(self.cache)
        self.cache.clear()
        logger.info("Cache cleared", entries_cleared=count)
    
    def _evict_entries(self):
        """Evict entries based on policy"""
        if self.policy == CachePolicy.LRU:
            # Evict least recently used
            if self.cache:
                lru_key = min(
                    self.cache.keys(),
                    key=lambda k: self.cache[k].last_accessed
                )
                del self.cache[lru_key]
                logger.debug("LRU cache entry evicted", key=lru_key)
        else:
            # Default: evict oldest
            if self.cache:
                oldest_key = min(
                    self.cache.keys(),
                    key=lambda k: self.cache[k].created_at
                )
                del self.cache[oldest_key]
                logger.debug("Oldest cache entry evicted", key=oldest_key)
    
    def cleanup_expired(self) -> int:
        """
        Remove expired entries
        
        Returns:
            Number of entries removed
        """
        expired_keys = [
            key for key, entry in self.cache.items()
            if entry.is_expired()
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.info(
                "Expired cache entries cleaned up",
                count=len(expired_keys)
            )
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'policy': self.policy,
            'default_ttl': self.default_ttl,
            'entries': [
                {
                    'key': key,
                    'created_at': entry.created_at.isoformat(),
                    'last_accessed': entry.last_accessed.isoformat(),
                    'access_count': entry.access_count,
                    'ttl': entry.ttl
                }
                for key, entry in self.cache.items()
            ]
        }


class ResultCache:
    """Result cache for workflow and agent results"""
    
    def __init__(self, cache_manager: Optional[CacheManager] = None):
        """
        Initialize result cache
        
        Args:
            cache_manager: Optional CacheManager instance
        """
        self.cache = cache_manager or CacheManager(
            max_size=1000,
            default_ttl=3600,  # 1 hour default
            policy=CachePolicy.TTL
        )
        logger.info("ResultCache initialized")
    
    def get_workflow_result(
        self,
        workflow_id: str,
        version: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Get cached workflow result"""
        key = f"workflow:{workflow_id}:{version or 'latest'}"
        return self.cache.get(key)
    
    def set_workflow_result(
        self,
        workflow_id: str,
        result: Dict[str, Any],
        ttl: Optional[float] = None,
        version: Optional[int] = None
    ):
        """Cache workflow result"""
        key = f"workflow:{workflow_id}:{version or 'latest'}"
        self.cache.set(key, result, ttl=ttl)
    
    def get_agent_result(
        self,
        agent_id: str,
        task_hash: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached agent result"""
        key = f"agent:{agent_id}:{task_hash}"
        return self.cache.get(key)
    
    def set_agent_result(
        self,
        agent_id: str,
        task_hash: str,
        result: Dict[str, Any],
        ttl: Optional[float] = None
    ):
        """Cache agent result"""
        key = f"agent:{agent_id}:{task_hash}"
        self.cache.set(key, result, ttl=ttl)
    
    def invalidate_workflow(self, workflow_id: str):
        """Invalidate all cached results for workflow"""
        pattern = f"workflow:{workflow_id}:"
        return self.cache.invalidate_pattern(pattern)
    
    def invalidate_agent(self, agent_id: str):
        """Invalidate all cached results for agent"""
        pattern = f"agent:{agent_id}:"
        return self.cache.invalidate_pattern(pattern)

