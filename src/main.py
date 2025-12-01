# src/main.py
from fastapi import FastAPI, Request, Depends, status
from fastapi.responses import JSONResponse          # ← THIS WAS MISSING
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from enum import Enum
from .deps import get_current_user   # ← your original function stays 100% unchanged

# This makes the green lock button appear in Swagger UI
security = HTTPBearer(auto_error=False)

class Tags(str, Enum):
    home = "Home"
    health = "Health Checks"
    users = "User Management"
    items = "Items"

app = FastAPI(
    title="HK EdTech API",
    version="2.0.0",
    description="Fully automated CI/CD → EC2 → Docker → Nginx → HTTPS ready",
    contact={"name": "Developer: milton chow", "email": "milton@gmail.com"},
    license_info={"name": "MIT"},
    # This line adds the Authorize button in Swagger/Redoc
    openapi_tags=[
        {"name": "Home", "description": "Protected endpoints"},
        {"name": "Health Checks", "description": "Public"},
        {"name": "User Management"},
        {"name": "Items"},
    ],
    # This makes the lock appear
    dependencies=[Depends(security)],   # ← important
)

# PUBLIC ENDPOINTS
@app.get("/health", tags=[Tags.health], include_in_schema=True)
async def health():
    return {"status": "healthy", "service": "fastapi-ec2-prod"}

# GLOBAL AUTH MIDDLEWARE (protects everything except the paths below)
@app.middleware("http")
async def supabase_auth_middleware(request: Request, call_next):
    # These paths are always public
    if request.url.path in {"/health", "/openapi.json", "/favicon.ico"} or \
       request.url.path.startswith(("/docs", "/redoc")):
        return await call_next(request)

    # Extract Bearer token manually (so your original get_current_user works unchanged)
    auth_header = request.headers.get("Authorization")
    credentials = None
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header[7:].strip()
        credentials = HTTPAuthorizationCredentials(scheme="bearer", credentials=token)

    try:
        user = await get_current_user(credentials)   # ← your original function, untouched
        request.state.user = user
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid or missing token"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    return await call_next(request)

# ALL ENDPOINTS BELOW ARE PROTECTED — no more Depends() spam!
@app.get("/", tags=[Tags.home])
async def read_root():
    return {"message": "Welcome, authenticated user!"}

@app.post("/users", tags=[Tags.users])
async def create_user(name: str, email: str):
    return {"id": 42, "name": name, "email": email}

@app.get("/users/{user_id}", tags=[Tags.users])
async def get_user(user_id: int):
    return {"id": user_id, "name": "Milton", "email": "milton@example.com"}

@app.put("/users/{user_id}", tags=[Tags.users])
async def update_user(user_id: int, name: str | None = None):
    return {"id": user_id, "updated": True, "name": name or "unchanged"}