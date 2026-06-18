"""
Security Module
Authentication, authorization, rate limiting, and input validation
"""

import os
import re
import hashlib
import secrets
from functools import wraps
from typing import Optional, Callable, List, Dict, Any
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, Security, Request, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator, Field
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
import redis

# Redis client for rate limiting
try:
    redis_client = redis.from_url(os.environ.get('REDIS_URL', 'redis://localhost:6379/0'))
    redis_client.ping()
    REDIS_AVAILABLE = True
except:
    redis_client = None
    REDIS_AVAILABLE = False

# Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', secrets.token_hex(32))
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24
RATE_LIMIT_REQUESTS = int(os.environ.get('RATE_LIMIT_REQUESTS', '100'))
RATE_LIMIT_WINDOW = int(os.environ.get('RATE_LIMIT_WINDOW', '3600'))  # 1 hour
MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB

# Security headers
SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';",
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
}

# Allowed CORS origins (production)
ALLOWED_ORIGINS = [
    'https://lovetrae.app',
    'https://www.lovetrae.app',
    'https://admin.lovetrae.app',
    'https://lovetrae.web.app',
    'https://lovetrae.firebaseapp.com',
    'app://lovetrae',
]

# Development origins (only in debug mode)
DEV_ORIGINS = [
    'http://localhost:3000',
    'http://localhost:19006',
    'http://localhost:19000',
    'http://localhost:8001',
    'exp://127.0.0.1:19000',
    'exp://localhost:19000',
]

# =============================================================================
# JWT Authentication
# =============================================================================

security = HTTPBearer(auto_error=False)


class TokenPayload(BaseModel):
    user_id: str
    email: Optional[str] = None
    exp: datetime
    iat: datetime
    type: str = 'access'


def create_jwt_token(user_id: str, email: Optional[str] = None, 
                     expires_delta: Optional[timedelta] = None) -> str:
    """Create a new JWT token"""
    now = datetime.now(timezone.utc)
    expires = now + (expires_delta or timedelta(hours=JWT_EXPIRATION_HOURS))
    
    payload = {
        'user_id': user_id,
        'email': email,
        'exp': expires,
        'iat': now,
        'type': 'access',
        'jti': secrets.token_hex(16),  # Unique token ID
    }
    
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except ExpiredSignatureError:
        return None
    except InvalidTokenError:
        return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> Optional[Dict[str, Any]]:
    """Dependency to get current authenticated user"""
    if not credentials:
        return None
    
    token = credentials.credentials
    payload = verify_jwt_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail='Invalid or expired token')
    
    return payload


async def require_auth(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> Dict[str, Any]:
    """Dependency that requires authentication"""
    if not credentials:
        raise HTTPException(status_code=401, detail='Authentication required')
    
    token = credentials.credentials
    payload = verify_jwt_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail='Invalid or expired token')
    
    return payload


def require_roles(required_roles: List[str]):
    """Decorator to require specific roles"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, current_user: Dict = Depends(require_auth), **kwargs):
            user_roles = current_user.get('roles', [])
            if not any(role in user_roles for role in required_roles):
                raise HTTPException(status_code=403, detail='Insufficient permissions')
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator


# =============================================================================
# Rate Limiting
# =============================================================================

class RateLimiter:
    """Rate limiter using Redis or in-memory fallback"""
    
    def __init__(self):
        self.memory_storage: Dict[str, Dict] = {}
    
    def _get_key(self, identifier: str, endpoint: str = 'global') -> str:
        """Generate rate limit key"""
        return f"rate_limit:{endpoint}:{identifier}"
    
    def is_allowed(self, identifier: str, endpoint: str = 'global', 
                   max_requests: int = RATE_LIMIT_REQUESTS,
                   window: int = RATE_LIMIT_WINDOW) -> tuple[bool, Dict]:
        """Check if request is allowed"""
        key = self._get_key(identifier, endpoint)
        now = datetime.now(timezone.utc).timestamp()
        
        if REDIS_AVAILABLE and redis_client:
            # Use Redis
            pipe = redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, now - window)
            pipe.zcard(key)
            pipe.zadd(key, {str(now): now})
            pipe.expire(key, window)
            _, current_count, _, _ = pipe.execute()
            
            allowed = current_count < max_requests
            remaining = max(0, max_requests - current_count - 1)
            reset_time = now + window
        else:
            # Use in-memory fallback
            if key not in self.memory_storage:
                self.memory_storage[key] = {'requests': [], 'reset_at': now + window}
            
            storage = self.memory_storage[key]
            
            # Clean old requests
            storage['requests'] = [
                req_time for req_time in storage['requests']
                if req_time > now - window
            ]
            
            current_count = len(storage['requests'])
            allowed = current_count < max_requests
            
            if allowed:
                storage['requests'].append(now)
            
            remaining = max(0, max_requests - current_count - 1)
            reset_time = storage.get('reset_at', now + window)
        
        return allowed, {
            'limit': max_requests,
            'remaining': remaining,
            'reset': int(reset_time),
            'window': window
        }


rate_limiter = RateLimiter()


async def rate_limit(request: Request, 
                     max_requests: int = RATE_LIMIT_REQUESTS,
                     window: int = RATE_LIMIT_WINDOW) -> Dict:
    """Rate limiting dependency"""
    # Get identifier (user ID if authenticated, else IP)
    client_ip = request.client.host if request.client else 'unknown'
    
    # Check for auth token
    auth_header = request.headers.get('authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        payload = verify_jwt_token(token)
        if payload:
            identifier = payload.get('user_id', client_ip)
        else:
            identifier = client_ip
    else:
        identifier = client_ip
    
    allowed, info = rate_limiter.is_allowed(identifier, 'global', max_requests, window)
    
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail={
                'error': 'Rate limit exceeded',
                'message': f'Too many requests. Try again in {window} seconds.',
                'retry_after': info['reset'] - int(datetime.now(timezone.utc).timestamp())
            }
        )
    
    return info


def rate_limit_decorator(max_requests: int = RATE_LIMIT_REQUESTS, 
                         window: int = RATE_LIMIT_WINDOW):
    """Decorator for rate limiting"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            await rate_limit(request, max_requests, window)
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator


# =============================================================================
# Input Validation & Sanitization
# =============================================================================

class SanitizedString(str):
    """String with sanitization applied"""
    pass


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """Sanitize user input string"""
    if not isinstance(value, str):
        return ''
    
    # Trim whitespace
    value = value.strip()
    
    # Limit length
    value = value[:max_length]
    
    # Remove null bytes
    value = value.replace('\x00', '')
    
    # Remove control characters except newlines and tabs
    value = ''.join(char for char in value if ord(char) >= 32 or char in '\n\t\r')
    
    # Prevent basic NoSQL injection attempts
    dangerous_patterns = [
        r'\$where',
        r'\$regex',
        r'\$ne',
        r'\$gt',
        r'\$lt',
        r'\$gte',
        r'\$lte',
        r'\$in',
        r'\$nin',
        r'\$exists',
        r'\$or',
        r'\$and',
    ]
    
    for pattern in dangerous_patterns:
        value = re.sub(pattern, '', value, flags=re.IGNORECASE)
    
    return value


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_uuid(value: str) -> bool:
    """Validate UUID format"""
    pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return re.match(pattern, value, re.IGNORECASE) is not None


class Validators:
    """Pydantic validators for common fields"""
    
    @staticmethod
    def validate_no_html(value: str) -> str:
        """Remove HTML tags"""
        if not isinstance(value, str):
            return value
        return re.sub(r'<[^>]+>', '', value)
    
    @staticmethod
    def validate_safe_string(value: str, max_length: int = 500) -> str:
        """Validate and sanitize string"""
        if not isinstance(value, str):
            raise ValueError('Must be a string')
        
        sanitized = sanitize_string(value, max_length)
        
        if len(sanitized) == 0 and len(value) > 0:
            raise ValueError('Contains only invalid characters')
        
        return sanitized


# =============================================================================
# Security Headers Middleware
# =============================================================================

def add_security_headers(response) -> None:
    """Add security headers to response"""
    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value
    
    # Add CORS headers based on origin
    # This is handled by FastAPI's CORS middleware, but we add additional checks here


def validate_origin(origin: Optional[str]) -> bool:
    """Validate request origin"""
    if not origin:
        return True  # Allow requests without origin (mobile apps)
    
    allowed = ALLOWED_ORIGINS.copy()
    
    if os.environ.get('DEBUG', 'false').lower() == 'true':
        allowed.extend(DEV_ORIGINS)
    
    return origin in allowed or any(
        origin.endswith(domain.replace('https://', '').replace('http://', ''))
        for domain in allowed
    )


# =============================================================================
# Request Size Limit
# =============================================================================

async def check_request_size(request: Request, max_size: int = MAX_REQUEST_SIZE):
    """Check if request body size is within limits"""
    content_length = request.headers.get('content-length')
    
    if content_length:
        size = int(content_length)
        if size > max_size:
            raise HTTPException(
                status_code=413,
                detail=f'Request body too large. Max size: {max_size} bytes'
            )


# =============================================================================
# Audit Logging
# =============================================================================

class AuditLogger:
    """Security audit logging"""
    
    @staticmethod
    def log_auth_attempt(success: bool, user_id: Optional[str], 
                         ip: str, reason: Optional[str] = None):
        """Log authentication attempt"""
        print(f"[AUDIT] Auth {'success' if success else 'failure'}: user={user_id}, ip={ip}, reason={reason}")
    
    @staticmethod
    def log_sos_trigger(user_id: str, couple_id: Optional[str], severity: int, ip: str):
        """Log SOS trigger"""
        print(f"[AUDIT] SOS triggered: user={user_id}, couple={couple_id}, severity={severity}, ip={ip}")
    
    @staticmethod
    def log_admin_action(admin_id: str, action: str, target: str, ip: str):
        """Log admin action"""
        print(f"[AUDIT] Admin action: admin={admin_id}, action={action}, target={target}, ip={ip}")
    
    @staticmethod
    def log_data_access(user_id: str, resource: str, action: str, ip: str):
        """Log sensitive data access"""
        print(f"[AUDIT] Data access: user={user_id}, resource={resource}, action={action}, ip={ip}")


audit_logger = AuditLogger()


# =============================================================================
# Password/Token Security
# =============================================================================

def hash_token(token: str) -> str:
    """Hash a token for storage (e.g., refresh tokens)"""
    return hashlib.sha256(token.encode()).hexdigest()


def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure token"""
    return secrets.token_urlsafe(length)


def constant_time_compare(val1: str, val2: str) -> bool:
    """Constant time comparison to prevent timing attacks"""
    return secrets.compare_digest(val1, val2)


# =============================================================================
# Export decorators
# =============================================================================

require_authentication = require_auth
require_admin = require_roles(['admin'])
require_moderator = require_roles(['admin', 'moderator'])

__all__ = [
    'create_jwt_token',
    'verify_jwt_token',
    'get_current_user',
    'require_auth',
    'require_authentication',
    'require_admin',
    'require_moderator',
    'require_roles',
    'rate_limit',
    'rate_limit_decorator',
    'rate_limiter',
    'sanitize_string',
    'validate_email',
    'validate_uuid',
    'Validators',
    'add_security_headers',
    'validate_origin',
    'check_request_size',
    'audit_logger',
    'hash_token',
    'generate_secure_token',
    'constant_time_compare',
    'SECURITY_HEADERS',
    'ALLOWED_ORIGINS',
    'JWT_SECRET',
]
