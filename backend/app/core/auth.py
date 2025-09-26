from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer()

async def require_auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Minimal auth dependency stub.
    - Accepts any Bearer token for now.
    - Replace with Supabase JWT verification later.
    """
    if not credentials or not credentials.scheme.lower() == "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    # TODO: verify JWT (Supabase) and attach user context
    return {"sub": "demo-user"}
