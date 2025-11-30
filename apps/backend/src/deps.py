from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import os

bearer_scheme = HTTPBearer(auto_error=False)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    # 1. Debug mode (so you can always access it while developing)
    debug_token = os.getenv("DEBUG_TOKEN", "super-secret-debug-token")
    if credentials and credentials.credentials == debug_token:
        return {"sub": "debug-user", "email": "you@localhost"}

    # 2. Real Supabase mode (only activates when secrets exist)
    secret = os.getenv("SUPABASE_JWT_SECRET")
    supabase_url = os.getenv("SUPABASE_URL")

    if secret and supabase_url and credentials:
        token = credentials.credentials
        try:
            payload = jwt.decode(token, secret, algorithms=["HS256"], audience="authenticated")
            if payload.get("iss") == f"{supabase_url}/auth/v1/token":
                return payload
        except JWTError:
            pass  # fall through to 401

    # 3. Nothing matched → deny
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing token",
        headers={"WWW-Authenticate": "Bearer"},
    )