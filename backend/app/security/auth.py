"""
Supabase JWT Authentication
Verifies JWT tokens using HS256 algorithm with JWT secret
"""
import os
from functools import lru_cache
from typing import Dict, Any

from jose import jwt, JWTError
from fastapi import Depends, HTTPException, Request, status
from loguru import logger


@lru_cache(maxsize=1)
def get_jwt_secret() -> str:
    """
    Get JWT secret for Supabase token verification.
    
    Supabase Auth uses HS256 (symmetric signing) with a shared secret.
    This is different from RS256/JWKS which uses public/private key pairs.
    
    Returns:
        JWT secret from environment
    
    Raises:
        ValueError if not configured
    """
    jwt_secret = os.getenv("SUPABASE_JWT_SECRET")
    
    if not jwt_secret:
        raise ValueError(
            "SUPABASE_JWT_SECRET must be set. "
            "Find it in Supabase Dashboard → Settings → API → JWT Secret"
        )
    
    logger.info("✅ JWT secret configured for HS256 verification")
    return jwt_secret


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


def verify_supabase_jwt(token: str, jwt_secret: str) -> Dict[str, Any]:
    """
    Verify Supabase JWT using HS256 algorithm.
    
    Supabase Auth tokens are signed with HS256 (symmetric key),
    not RS256 (asymmetric JWKS). We verify using the JWT secret.
    
    Args:
        token: Access token from Supabase Auth
        jwt_secret: JWT secret from Supabase project settings
    
    Returns:
        Decoded JWT payload containing user info
    
    Raises:
        HTTPException 401 if invalid or expired
    """
    try:
        # Decode and verify token with HS256
        payload = jwt.decode(
            token,
            jwt_secret,
            algorithms=["HS256"],
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_aud": False,  # Supabase doesn't require aud verification
            }
        )
        
        logger.debug(f"✅ JWT verified for user: {payload.get('email', 'unknown')}")
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.warning("JWT verification failed: token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
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
    jwt_secret: str = Depends(get_jwt_secret)
) -> Dict[str, Any]:
    """
    Dependency to get current authenticated user from JWT.
    
    Verifies Supabase JWT token and extracts user information.
    
    Returns:
        Dict with user_id and email from JWT payload
    
    Raises:
        HTTPException 401 if invalid or expired token
    """
    payload = verify_supabase_jwt(token, jwt_secret)
    
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
