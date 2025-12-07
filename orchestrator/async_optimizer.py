"""
Async Optimization
Optimize async operations, batch processing, and lazy loading
"""

import asyncio
from typing import Dict, Any, List, Optional, Callable, TypeVar, Awaitable
from datetime import datetime
from monitoring import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


class AsyncOptimizer:
    """
    Async operation optimizer
    
    Features:
    - Batch processing
    - Lazy loading
    - Async operation optimization
    """
    
    def __init__(self):
        """Initialize async optimizer"""
        self.batch_processors: Dict[str, List[Any]] = {}
        logger.info("AsyncOptimizer initialized")
    
    async def batch_execute(
        self,
        tasks: List[Awaitable[T]],
        batch_size: int = 10,
        max_concurrent: Optional[int] = None
    ) -> List[T]:
        """
        Execute tasks in batches with concurrency control
        
        Args:
            tasks: List of async tasks
            batch_size: Number of tasks per batch
            max_concurrent: Maximum concurrent tasks (None = no limit)
            
        Returns:
            List of results
        """
        results = []
        
        # Process in batches
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            
            logger.debug(
                "Processing batch",
                batch_num=i // batch_size + 1,
                batch_size=len(batch),
                total_tasks=len(tasks)
            )
            
            if max_concurrent:
                # Use semaphore to limit concurrency
                semaphore = asyncio.Semaphore(max_concurrent)
                
                async def bounded_task(task):
                    async with semaphore:
                        return await task
                
                batch_results = await asyncio.gather(
                    *[bounded_task(task) for task in batch],
                    return_exceptions=True
                )
            else:
                batch_results = await asyncio.gather(*batch, return_exceptions=True)
            
            results.extend(batch_results)
        
        return results
    
    async def execute_with_semaphore(
        self,
        tasks: List[Awaitable[T]],
        max_concurrent: int = 5
    ) -> List[T]:
        """
        Execute tasks with semaphore-based concurrency control
        
        Args:
            tasks: List of async tasks
            max_concurrent: Maximum concurrent tasks
            
        Returns:
            List of results
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def bounded_task(task):
            async with semaphore:
                return await task
        
        return await asyncio.gather(
            *[bounded_task(task) for task in tasks],
            return_exceptions=True
        )


class LazyLoader:
    """Lazy loading helper for deferred data loading"""
    
    def __init__(self, loader: Callable[[], Awaitable[T]]):
        """
        Initialize lazy loader
        
        Args:
            loader: Async function to load data
        """
        self.loader = loader
        self._value: Optional[T] = None
        self._loaded = False
        self._loading = False
    
    async def get(self) -> T:
        """Get value, loading if not already loaded"""
        if self._loaded:
            return self._value
        
        if self._loading:
            # Wait for ongoing load
            while self._loading:
                await asyncio.sleep(0.1)
            return self._value
        
        # Load value
        self._loading = True
        try:
            self._value = await self.loader()
            self._loaded = True
            return self._value
        finally:
            self._loading = False
    
    def invalidate(self):
        """Invalidate cached value"""
        self._loaded = False
        self._value = None
    
    def is_loaded(self) -> bool:
        """Check if value is loaded"""
        return self._loaded

