"""
DEPRECATED: This module is kept for backward compatibility.
Use app.security.auth instead.

This file now acts as a compatibility shim that redirects to the new auth system.

Migration note: When USE_RBAC=false, uses legacy stub for backward compatibility.
When USE_RBAC=true, redirects to new Supabase JWT auth.
"""
import os
from loguru import logger
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# Check if we should use the new auth system
use_rbac = os.getenv("USE_RBAC", "false").lower() == "true"

if use_rbac:
    # Import new auth system
    logger.info("🔄 core/auth.py redirecting to security/auth.py (RBAC enabled)")
    from app.security.auth import get_current_user as require_auth
    
else:
    # Legacy stub for development/testing (backward compatibility)
    logger.warning("⚠️  Using legacy auth stub in core/auth.py (set USE_RBAC=true for production)")
    
    security = HTTPBearer()
    
    async def require_auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
        """
        Legacy auth dependency stub (DEPRECATED).
        Accepts any Bearer token for backward compatibility.
        
        Migration: Set USE_RBAC=true to use Supabase JWT verification.
        """
        if not credentials or not credentials.scheme.lower() == "bearer":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
        return {"sub": "demo-user", "email": "demo@localhost", "user_id": "demo-user"}
