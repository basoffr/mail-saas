"""
Role-Based Access Control (RBAC)
Checks user roles from profiles table
"""
import os
from typing import Dict, Any, Tuple
from functools import lru_cache
import time

from fastapi import Depends, HTTPException, status
from loguru import logger

from app.security.auth import get_auth_dependency


class RoleCache:
    """
    Simple in-memory cache for user roles.
    Reduces DB queries with 60s TTL.
    """
    
    def __init__(self, ttl: int = 60):
        self.ttl = ttl
        self._cache: Dict[str, Tuple[str, float]] = {}  # {user_id: (role, expiry)}
    
    def get(self, user_id: str) -> str | None:
        """Get cached role if not expired"""
        if user_id in self._cache:
            role, expiry = self._cache[user_id]
            if time.time() < expiry:
                return role
            else:
                del self._cache[user_id]
        return None
    
    def set(self, user_id: str, role: str):
        """Cache role with TTL"""
        self._cache[user_id] = (role, time.time() + self.ttl)
    
    def clear(self):
        """Clear entire cache"""
        self._cache.clear()


@lru_cache(maxsize=1)
def get_role_cache() -> RoleCache:
    """Singleton role cache instance"""
    return RoleCache(ttl=60)


async def get_user_role(user_id: str) -> str | None:
    """
    Get user role from profiles table.
    
    Args:
        user_id: Supabase Auth user UUID
    
    Returns:
        'admin' or 'viewer' or None if not found
    """
    # Check cache first
    role_cache = get_role_cache()
    cached_role = role_cache.get(user_id)
    
    if cached_role:
        logger.debug(f"Role cache hit for user {user_id}: {cached_role}")
        return cached_role
    
    # Fetch from database
    try:
        # Use local get_supabase_client function (defined below)
        supabase = _get_supabase_client()
        if not supabase:
            # Fallback: no Supabase connection
            logger.warning("Supabase not available for role lookup")
            return None
        
        response = supabase.table("profiles").select("role").eq("user_id", user_id).single().execute()
        
        if response.data:
            role = response.data.get("role")
            logger.info(f"✅ Fetched role for user {user_id}: {role}")
            
            # Cache it
            role_cache.set(user_id, role)
            
            return role
        else:
            logger.warning(f"No profile found for user {user_id}")
            return None
            
    except Exception as e:
        logger.error(f"Failed to fetch role for user {user_id}: {e}")
        return None


def require_role(*allowed_roles: str):
    """
    RBAC dependency factory.
    
    Usage:
        @router.get("/admin-only", dependencies=[Depends(require_role("admin"))])
        @router.get("/stats", dependencies=[Depends(require_role("admin", "viewer"))])
    
    Args:
        *allowed_roles: Tuple of allowed roles ('admin', 'viewer')
    
    Returns:
        FastAPI dependency function
    """
    
    async def dependency(user: Dict[str, Any] = Depends(get_auth_dependency())):
        """Check if user has required role"""
        user_id = user["user_id"]
        
        # Get role from DB
        role = await get_user_role(user_id)
        
        if not role:
            logger.warning(f"User {user_id} has no role assigned")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no role assigned. Contact administrator."
            )
        
        if role not in allowed_roles:
            logger.warning(
                f"User {user_id} with role '{role}' attempted to access "
                f"resource requiring roles: {allowed_roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {', '.join(allowed_roles)}"
            )
        
        # Add role to user object for downstream use
        user["role"] = role
        
        logger.debug(f"✅ User {user_id} authorized with role '{role}'")
        
        return user
    
    return dependency


# Convenience dependencies
require_admin = require_role("admin")
require_admin_or_viewer = require_role("admin", "viewer")


# Helper to get Supabase client for role lookups
def _get_supabase_client():
    """
    Get Supabase client for role lookups.
    
    Uses service role key for admin access to profiles table.
    """
    try:
        from supabase import create_client
        
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_key:
            logger.warning("Supabase credentials not configured")
            return None
        
        return create_client(supabase_url, supabase_key)
    except Exception as e:
        logger.error(f"Failed to create Supabase client: {e}")
        return None
