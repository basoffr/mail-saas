"""
Authentication API endpoints
"""
from typing import Dict, Any

from fastapi import APIRouter, Depends
from loguru import logger

from app.security.auth import get_auth_dependency
from app.security.rbac import get_user_role
from app.schemas.common import DataResponse


router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


@router.get("/me", response_model=DataResponse[Dict[str, Any]])
async def get_current_user_info(user: Dict[str, Any] = Depends(get_auth_dependency())):
    """
    Get current authenticated user info including role.
    
    Returns:
        {
            "user_id": "uuid",
            "email": "user@example.com",
            "role": "admin" | "viewer"
        }
    """
    try:
        user_id = user["user_id"]
        email = user["email"]
        
        # Get role from profiles table
        role = await get_user_role(user_id)
        
        if not role:
            logger.warning(f"User {user_id} has no role assigned")
            return DataResponse(
                data=None,
                error="User has no role assigned. Contact administrator."
            )
        
        logger.info(f"User info requested: {email} (role: {role})")
        
        return DataResponse(
            data={
                "user_id": user_id,
                "email": email,
                "role": role
            },
            error=None
        )
        
    except Exception as e:
        logger.error(f"Error fetching user info: {e}")
        return DataResponse(
            data=None,
            error=f"Failed to fetch user info: {str(e)}"
        )


@router.post("/logout")
async def logout():
    """
    Logout endpoint (client-side token removal).
    Backend is stateless, so this is mainly for logging.
    """
    logger.info("User logged out (client-side token removal)")
    return DataResponse(
        data={"message": "Logged out successfully"},
        error=None
    )
