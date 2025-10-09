"""
Supabase JWT Authentication
Verifies JWT tokens via JWKS endpoint
"""
import os
import time
from functools import lru_cache
from typing import Dict, Any, Optional

import requests
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, Request, status
from loguru import logger


class JWKSCache:
    """
    Cache for JWKS (JSON Web Key Set) from Supabase.
    Reduces external calls by caching keys with TTL.
    """
    
    def __init__(self, url: str, ttl: int = 3600):
        """
        Args:
            url: JWKS endpoint URL (e.g., https://xxx.supabase.co/auth/v1/.well-known/jwks.json)
            ttl: Time to live in seconds (default: 1 hour)
        """
        self.url = url
        self.ttl = ttl
        self._exp = 0
        self._jwks: Optional[Dict[str, Any]] = None
    
    def get(self) -> Dict[str, Any]:
        """Get JWKS, fetching from remote if expired"""
        now = time.time()
        
        if not self._jwks or now > self._exp:
            try:
                logger.debug(f"Fetching JWKS from {self.url}")
                response = requests.get(self.url, timeout=5)
                response.raise_for_status()
                self._jwks = response.json()
                self._exp = now + self.ttl
                logger.info(f"✅ JWKS cached (expires in {self.ttl}s)")
            except Exception as e:
                logger.error(f"Failed to fetch JWKS: {e}")
                if not self._jwks:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="Cannot verify tokens: JWKS unavailable"
                    )
        
        return self._jwks


@lru_cache(maxsize=1)
def get_jwks_cache() -> JWKSCache:
    """Singleton JWKS cache instance"""
    jwks_url = os.getenv("SUPABASE_JWKS_URL")
    
    if not jwks_url:
        # Fallback: construct from SUPABASE_URL
        supabase_url = os.getenv("SUPABASE_URL")
        if not supabase_url:
            raise ValueError("SUPABASE_URL or SUPABASE_JWKS_URL must be set")
        jwks_url = f"{supabase_url}/auth/v1/.well-known/jwks.json"
    
    logger.info(f"Initialized JWKS cache: {jwks_url}")
    return JWKSCache(jwks_url)


def bearer_token(request: Request) -> str:
    """
    Extract Bearer token from Authorization header.
    
    Raises:
        HTTPException 401 if missing or malformed
    """
    auth_header = request.headers.get("Authorization", "")
    
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return auth_header.split(" ", 1)[1]


def verify_supabase_jwt(token: str, jwks_cache: JWKSCache) -> Dict[str, Any]:
    """
    Verify Supabase JWT using JWKS.
    
    Args:
        token: Access token from Supabase Auth
        jwks_cache: JWKS cache instance
    
    Returns:
        Decoded JWT payload
    
    Raises:
        HTTPException 401 if invalid
    """
    try:
        # Get JWKS keys
        jwks = jwks_cache.get()
        
        # Get token header to find matching key
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        
        if not kid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing kid"
            )
        
        # Find matching key
        key = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
        
        if not key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: unknown key ID"
            )
        
        # Verify and decode token
        payload = jwt.decode(
            token,
            key,
            algorithms=[key.get("alg", "RS256")],
            options={"verify_aud": False}  # Supabase doesn't use aud claim
        )
        
        return payload
        
    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token verification failed"
        )


async def get_current_user(
    token: str = Depends(bearer_token),
    jwks_cache: JWKSCache = Depends(get_jwks_cache)
) -> Dict[str, Any]:
    """
    Dependency to get current authenticated user.
    
    Returns:
        Dict with user_id and email
    
    Raises:
        HTTPException 401 if invalid token
    """
    payload = verify_supabase_jwt(token, jwks_cache)
    
    user_id = payload.get("sub")
    email = payload.get("email") or payload.get("user_metadata", {}).get("email")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user ID"
        )
    
    return {
        "user_id": user_id,
        "email": email
    }


# Optional: Simple mock for development without Supabase
async def get_current_user_mock() -> Dict[str, Any]:
    """Mock user for development (set USE_AUTH_MOCK=true)"""
    return {
        "user_id": "00000000-0000-0000-0000-000000000000",
        "email": "dev@localhost"
    }


def get_auth_dependency():
    """
    Get appropriate auth dependency based on environment.
    
    Returns:
        get_current_user or get_current_user_mock
    """
    use_mock = os.getenv("USE_AUTH_MOCK", "false").lower() == "true"
    
    if use_mock:
        logger.warning("⚠️  Using MOCK authentication (dev only)")
        return get_current_user_mock
    
    return get_current_user
