from fastapi import FastAPI, Depends, Request, HTTPException, status
from enum import Enum
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .deps import get_current_user

bearer_scheme = HTTPBearer(auto_error=False)

class Tags(str, Enum):
    """Color-coded tags for the Swagger UI"""
    home = "Home"
    health = "Health Checks"
    users = "User Management"
    items = "Items"


app = FastAPI(
    title="HK EdTech API",
    description="Fully automated CI/CD → EC2 → Docker → Nginx → HTTPS ready",
    version="2.0.0",
    contact={
        "name": "Developer: milton chow",
        "email": "milton@gmail.com",
    },
    license_info={"name": "MIT"},
)

# Health (Anyone can call this)
@app.get("/health", tags=[Tags.health])
def health():
    return {"status": "healthy", "service": "fastapi-ec2-prod"}

# GLOBAL AUTH MIDDLEWARE — protects EVERYTHING below (except the ones above)
@app.middleware("http")
async def supabase_auth_middleware(request: Request, call_next):
    # Let these paths through without auth (including Swagger UI files)
    if request.url.path in {"/health"} or request.url.path.startswith((
        "/docs", "/redoc", "/openapi.json", "/favicon.ico"
    )):
        return await call_next(request)

    # Extract Bearer token the same way your original deps.py does
    auth = request.headers.get("Authorization")
    if auth and auth.lower().startswith("bearer "):
        token = auth[len("bearer "):].strip()
        credentials = HTTPAuthorizationCredentials(scheme="bearer", credentials=token)
    else:
        credentials = None

    # Use your **existing** get_current_user exactly as it was written
    try:
        user = await get_current_user(credentials)  # ← unchanged!
        request.state.user = user
    except HTTPException as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers={"WWW-Authenticate": "Bearer"},
        )

    return await call_next(request)


# Home - Protecting ALL routes (or just specific ones)
@app.get("/", tags=[Tags.home])
# def read_root(user = Depends(get_current_user)):
def read_root():
    return {"message": "Welcome, authenticated user!"}

# Example CRUD endpoints with perfect colors in Swagger
@app.post("/users", tags=[Tags.users], summary="Create a new user")
def create_user(name: str, email: str):
    return {"id": 42, "name": name, "email": email}

@app.get("/users/{user_id}", tags=[Tags.users], summary="Get user by ID")
def get_user(user_id: int):
    return {"id": user_id, "name": "Milton", "email": "milton@example.com"}

@app.put("/users/{user_id}", tags=[Tags.users], summary="Update user")
def update_user(user_id: int, name: str | None = None):
    return {"id": user_id, "updated": True, "name": name or "unchanged"}
