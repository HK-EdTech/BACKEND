from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from jose.exceptions import JWKError
import httpx
import os
from typing import Dict, Any

bearer_scheme = HTTPBearer(auto_error=False)

async def get_public_key(kid: str, supabase_url: str) -> Dict[str, Any]:
    """Fetch the public key from Supabase JWKS endpoint."""
    jwks_url = f"{supabase_url}/auth/v1/jwks"
    async with httpx.AsyncClient() as client:
        response = await client.get(jwks_url)
        response.raise_for_status()
        jwks = response.json()
    
    # Find the key matching the kid
    for key in jwks["keys"]:
        if key["kid"] == kid:
            return key
    raise HTTPException(status_code=401, detail="Public key not found")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> Dict[str, Any]:
    supabase_url = os.getenv("SUPABASE_URL")
    
    # Debug mode (always works for dev)
    debug_token = os.getenv("DEBUG_TOKEN", "super-secret-debug-token")
    if credentials and credentials.credentials == debug_token:
        return {"sub": "debug-user", "email": "you@localhost"}

    # Real Supabase JWT verification (new signing keys)
    if not supabase_url or not credentials:
        raise HTTPException(status_code=401, detail="Missing token or Supabase URL")

    token = credentials.credentials
    try:
        # Get unverified header to extract kid
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        if not kid:
            raise JWTError("No kid in token")

        # Fetch matching public key
        public_key = await get_public_key(kid, supabase_url)

        # Verify token with public key
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["ES256"],  # ECC P-256 = ES256
            audience="authenticated",
            options={"verify_signature": True},
        )

        # Verify issuer
        if payload.get("iss") != f"{supabase_url}/auth/v1/":
            raise JWTError("Invalid issuer")

        return payload
    except (JWTError, JWKError, httpx.HTTPError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")