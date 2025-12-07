"""
Connection Pooling
HTTP and database connection pooling for optimal resource usage
"""

import asyncio
from typing import Optional, Dict, Any, Callable, List
import aiohttp
from aiohttp import ClientSession, TCPConnector
from monitoring import get_logger

logger = get_logger(__name__)


class ConnectionPoolManager:
    """
    Connection pool manager for HTTP and database connections
    
    Features:
    - HTTP client connection pooling
    - Connection reuse
    - Resource optimization
    """
    
    def __init__(
        self,
        max_connections: int = 100,
        max_connections_per_host: int = 30,
        ttl: Optional[float] = None
    ):
        """
        Initialize connection pool manager
        
        Args:
            max_connections: Maximum total connections
            max_connections_per_host: Maximum connections per host
            ttl: Optional connection TTL
        """
        self.max_connections = max_connections
        self.max_connections_per_host = max_connections_per_host
        self.ttl = ttl
        
        self.http_session: Optional[ClientSession] = None
        
        logger.info(
            "ConnectionPoolManager initialized",
            max_connections=max_connections,
            max_per_host=max_connections_per_host
        )
    
    async def get_http_session(self) -> ClientSession:
        """
        Get or create HTTP session with connection pooling
        
        Returns:
            aiohttp ClientSession
        """
        if self.http_session is None or self.http_session.closed:
            connector = TCPConnector(
                limit=self.max_connections,
                limit_per_host=self.max_connections_per_host,
                ttl_dns_cache=self.ttl if self.ttl else 300,
                enable_cleanup_closed=True
            )
            
            timeout = aiohttp.ClientTimeout(
                total=30,
                connect=10,
                sock_read=10
            )
            
            self.http_session = ClientSession(
                connector=connector,
                timeout=timeout
            )
            
            logger.info("HTTP session created with connection pooling")
        
        return self.http_session
    
    async def close(self):
        """Close all connection pools"""
        if self.http_session and not self.http_session.closed:
            await self.http_session.close()
            self.http_session = None
            logger.info("HTTP session closed")


class BatchProcessor:
    """
    Batch processor for async operations
    
    Features:
    - Batch processing
    - Automatic batching
    - Batch timeout
    """
    
    def __init__(
        self,
        batch_size: int = 10,
        batch_timeout: float = 5.0
    ):
        """
        Initialize batch processor
        
        Args:
            batch_size: Maximum batch size
            batch_timeout: Timeout in seconds before processing batch
        """
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.batches: Dict[str, list] = {}
        logger.info(
            "BatchProcessor initialized",
            batch_size=batch_size,
            timeout=batch_timeout
        )
    
    async def add_to_batch(
        self,
        batch_key: str,
        item: Any,
        processor: callable
    ) -> Any:
        """
        Add item to batch and process if batch is full
        
        Args:
            batch_key: Batch identifier
            item: Item to add
            processor: Function to process batch
            
        Returns:
            Result for this item
        """
        if batch_key not in self.batches:
            self.batches[batch_key] = []
        
        batch = self.batches[batch_key]
        batch.append(item)
        
        # Process if batch is full
        if len(batch) >= self.batch_size:
            return await self._process_batch(batch_key, processor)
        
        # TODO: Implement timeout-based processing
        # For now, return None (would need async task for timeout)
        return None
    
    async def _process_batch(
        self,
        batch_key: str,
        processor: callable
    ) -> Any:
        """Process batch"""
        batch = self.batches.pop(batch_key, [])
        if batch:
            if asyncio.iscoroutinefunction(processor):
                return await processor(batch)
            else:
                return processor(batch)
        return None

