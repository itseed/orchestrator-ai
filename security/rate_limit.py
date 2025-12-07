"""
Rate Limiting
API rate limiting to prevent abuse
"""

from typing import Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from fastapi import Request, HTTPException
from monitoring import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """
    Rate limiter using token bucket algorithm
    
    Features:
    - Per-user rate limiting
    - Per-IP rate limiting
    - Configurable limits
    - Sliding window
    """
    
    def __init__(
        self,
        default_requests: int = 100,
        default_window: int = 60,  # seconds
        per_user_limits: Optional[Dict[str, Dict[str, int]]] = None
    ):
        """
        Initialize rate limiter
        
        Args:
            default_requests: Default number of requests allowed
            default_window: Default time window in seconds
            per_user_limits: Optional per-user limits {user_id: {requests: int, window: int}}
        """
        self.default_requests = default_requests
        self.default_window = default_window
        self.per_user_limits = per_user_limits or {}
        
        # Store request timestamps: {identifier: [timestamps]}
        self.request_history: Dict[str, list] = defaultdict(list)
        
        logger.info(
            "RateLimiter initialized",
            default_requests=default_requests,
            default_window=default_window
        )
    
    def _get_identifier(self, request: Request, user_id: Optional[str] = None) -> str:
        """
        Get identifier for rate limiting
        
        Args:
            request: FastAPI request
            user_id: Optional user ID
            
        Returns:
            Identifier string
        """
        if user_id:
            return f"user:{user_id}"
        
        # Fallback to IP address
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"
    
    def _cleanup_old_requests(self, identifier: str, window: int):
        """Remove old requests outside the time window"""
        if identifier not in self.request_history:
            return
        
        cutoff_time = datetime.utcnow() - timedelta(seconds=window)
        self.request_history[identifier] = [
            ts for ts in self.request_history[identifier]
            if ts > cutoff_time
        ]
    
    def is_allowed(
        self,
        request: Request,
        user_id: Optional[str] = None,
        custom_requests: Optional[int] = None,
        custom_window: Optional[int] = None
    ) -> tuple[bool, Dict[str, int]]:
        """
        Check if request is allowed
        
        Args:
            request: FastAPI request
            user_id: Optional user ID
            custom_requests: Optional custom request limit
            custom_window: Optional custom window
            
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        identifier = self._get_identifier(request, user_id)
        
        # Get limits for this identifier
        if identifier.startswith("user:") and identifier in self.per_user_limits:
            limits = self.per_user_limits[identifier]
            max_requests = custom_requests or limits.get('requests', self.default_requests)
            window = custom_window or limits.get('window', self.default_window)
        else:
            max_requests = custom_requests or self.default_requests
            window = custom_window or self.default_window
        
        # Cleanup old requests
        self._cleanup_old_requests(identifier, window)
        
        # Check current count
        current_count = len(self.request_history[identifier])
        
        rate_limit_info = {
            'limit': max_requests,
            'remaining': max(0, max_requests - current_count),
            'reset_in': window
        }
        
        if current_count >= max_requests:
            logger.warning(
                "Rate limit exceeded",
                identifier=identifier,
                count=current_count,
                limit=max_requests
            )
            return False, rate_limit_info
        
        # Add current request
        self.request_history[identifier].append(datetime.utcnow())
        
        return True, rate_limit_info
    
    def reset(self, identifier: str):
        """Reset rate limit for identifier"""
        if identifier in self.request_history:
            del self.request_history[identifier]
            logger.info("Rate limit reset", identifier=identifier)


class RateLimitMiddleware:
    """Rate limiting middleware for FastAPI"""
    
    def __init__(
        self,
        rate_limiter: Optional[RateLimiter] = None,
        enabled: bool = True,
        skip_paths: Optional[list] = None
    ):
        """
        Initialize rate limit middleware
        
        Args:
            rate_limiter: Optional RateLimiter instance
            enabled: Whether rate limiting is enabled
            skip_paths: List of paths to skip rate limiting
        """
        self.rate_limiter = rate_limiter or RateLimiter()
        self.enabled = enabled
        self.skip_paths = skip_paths or ['/health', '/docs', '/openapi.json']
        logger.info("RateLimitMiddleware initialized", enabled=enabled)
    
    async def __call__(self, request: Request, call_next):
        """Process request with rate limiting"""
        # Skip rate limiting for certain paths
        if request.url.path in self.skip_paths:
            return await call_next(request)
        
        if not self.enabled:
            return await call_next(request)
        
        # Get user ID from request if available
        user_id = request.state.get('user_id') if hasattr(request.state, 'user_id') else None
        
        # Check rate limit
        is_allowed, rate_limit_info = self.rate_limiter.is_allowed(request, user_id=user_id)
        
        if not is_allowed:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={
                    "X-RateLimit-Limit": str(rate_limit_info['limit']),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(rate_limit_info['reset_in'])
                }
            )
        
        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(rate_limit_info['limit'])
        response.headers["X-RateLimit-Remaining"] = str(rate_limit_info['remaining'])
        response.headers["X-RateLimit-Reset"] = str(rate_limit_info['reset_in'])
        
        return response

