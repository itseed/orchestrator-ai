"""
Authentication
API key and JWT token authentication
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import secrets
from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from monitoring import get_logger
from config.settings import get_settings

logger = get_logger(__name__)
settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# API Key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# JWT Bearer token
bearer_scheme = HTTPBearer(auto_error=False)


class APIKeyAuth:
    """API Key authentication"""
    
    def __init__(self, api_keys: Optional[Dict[str, Dict[str, Any]]] = None):
        """
        Initialize API key authentication
        
        Args:
            api_keys: Dictionary of API keys and their metadata
                     Format: {api_key: {user_id: str, permissions: list, ...}}
        """
        self.api_keys = api_keys or {}
        
        # Load API key from settings if available
        if settings.API_KEY:
            self.api_keys[settings.API_KEY] = {
                'user_id': 'system',
                'permissions': ['*'],  # All permissions
                'created_at': datetime.utcnow().isoformat()
            }
        
        logger.info("APIKeyAuth initialized", keys_count=len(self.api_keys))
    
    def validate_api_key(self, api_key: Optional[str]) -> Dict[str, Any]:
        """
        Validate API key
        
        Args:
            api_key: API key to validate
            
        Returns:
            User metadata if valid
            
        Raises:
            HTTPException if invalid
        """
        if not api_key:
            raise HTTPException(
                status_code=401,
                detail="API key is required",
                headers={"WWW-Authenticate": "ApiKey"}
            )
        
        key_data = self.api_keys.get(api_key)
        if not key_data:
            logger.warning("Invalid API key attempted", api_key_prefix=api_key[:8] if api_key else None)
            raise HTTPException(
                status_code=401,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "ApiKey"}
            )
        
        logger.debug("API key validated", user_id=key_data.get('user_id'))
        return key_data
    
    def create_api_key(self, user_id: str, permissions: Optional[list] = None) -> str:
        """
        Create a new API key
        
        Args:
            user_id: User ID
            permissions: Optional list of permissions
            
        Returns:
            New API key
        """
        api_key = secrets.token_urlsafe(32)
        self.api_keys[api_key] = {
            'user_id': user_id,
            'permissions': permissions or [],
            'created_at': datetime.utcnow().isoformat()
        }
        
        logger.info("API key created", user_id=user_id)
        return api_key
    
    def revoke_api_key(self, api_key: str) -> bool:
        """Revoke an API key"""
        if api_key in self.api_keys:
            del self.api_keys[api_key]
            logger.info("API key revoked", api_key_prefix=api_key[:8])
            return True
        return False


class JWTAuth:
    """JWT token authentication"""
    
    def __init__(
        self,
        secret_key: Optional[str] = None,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30
    ):
        """
        Initialize JWT authentication
        
        Args:
            secret_key: Secret key for JWT (uses settings.SECRET_KEY if not provided)
            algorithm: JWT algorithm
            access_token_expire_minutes: Token expiration time in minutes
        """
        self.secret_key = secret_key or settings.SECRET_KEY or "change-this-secret-key-in-production"
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        
        logger.info("JWTAuth initialized")
    
    def create_access_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT access token
        
        Args:
            data: Data to encode in token
            expires_delta: Optional expiration delta
            
        Returns:
            Encoded JWT token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        
        logger.debug("Access token created", user_id=data.get('sub'))
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode JWT token
        
        Args:
            token: JWT token to verify
            
        Returns:
            Decoded token payload
            
        Raises:
            HTTPException if invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            logger.warning("Invalid JWT token", error=str(e))
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"}
            )
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def hash_password(self, password: str) -> str:
        """Hash password"""
        return pwd_context.hash(password)


# Global instances
_api_key_auth: Optional[APIKeyAuth] = None
_jwt_auth: Optional[JWTAuth] = None


def get_api_key_auth() -> APIKeyAuth:
    """Get global API key auth instance"""
    global _api_key_auth
    if _api_key_auth is None:
        _api_key_auth = APIKeyAuth()
    return _api_key_auth


def get_jwt_auth() -> JWTAuth:
    """Get global JWT auth instance"""
    global _jwt_auth
    if _jwt_auth is None:
        _jwt_auth = JWTAuth()
    return _jwt_auth


async def authenticate_api_key(
    api_key: Optional[str] = Security(api_key_header)
) -> Dict[str, Any]:
    """
    FastAPI dependency for API key authentication
    
    Args:
        api_key: API key from header
        
    Returns:
        User metadata
    """
    auth = get_api_key_auth()
    return auth.validate_api_key(api_key)


async def authenticate_jwt(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme)
) -> Dict[str, Any]:
    """
    FastAPI dependency for JWT authentication
    
    Args:
        credentials: Bearer token credentials
        
    Returns:
        Decoded token payload
    """
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    auth = get_jwt_auth()
    return auth.verify_token(credentials.credentials)


def get_current_user(
    api_key: Optional[str] = Security(api_key_header),
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme)
) -> Dict[str, Any]:
    """
    Get current authenticated user (supports both API key and JWT)
    
    Args:
        api_key: Optional API key
        credentials: Optional JWT credentials
        
    Returns:
        User information
    """
    # Try API key first
    if api_key:
        try:
            auth = get_api_key_auth()
            return auth.validate_api_key(api_key)
        except HTTPException:
            pass
    
    # Try JWT
    if credentials:
        try:
            auth = get_jwt_auth()
            payload = auth.verify_token(credentials.credentials)
            return {
                'user_id': payload.get('sub'),
                'permissions': payload.get('permissions', []),
                'auth_method': 'jwt'
            }
        except HTTPException:
            pass
    
    # No valid authentication
    raise HTTPException(
        status_code=401,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer, ApiKey"}
    )


class AuthenticationMiddleware:
    """Authentication middleware for FastAPI"""
    
    def __init__(self, enable_auth: bool = True):
        """
        Initialize authentication middleware
        
        Args:
            enable_auth: Whether to enable authentication (useful for development)
        """
        self.enable_auth = enable_auth
        logger.info("AuthenticationMiddleware initialized", enabled=enable_auth)
    
    async def __call__(self, request, call_next):
        """Process request with authentication"""
        # Skip auth for public endpoints
        if request.url.path in ['/health', '/docs', '/openapi.json', '/metrics']:
            return await call_next(request)
        
        if not self.enable_auth:
            return await call_next(request)
        
        # Authentication is handled by dependencies
        # This middleware can be used for logging or other purposes
        response = await call_next(request)
        return response

