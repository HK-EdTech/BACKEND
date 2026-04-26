# src/main.py
from dotenv import load_dotenv
load_dotenv()  # Load environment variables first

import os

import httpx
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from enum import Enum
from contextlib import asynccontextmanager
from pydantic import BaseModel
from google.cloud import vision

from .deps import get_current_user
from .database import connect_db, disconnect_db
from .ocrs.models.GoogleCloudVisionAPI import GoogleCloudVisionAPI

# Import routers from modules
from .modules.profile.profile_controller import router as profile_router
from .modules.scan_and_mark.scan_and_upload.scan_and_upload_controller import router as scan_and_upload_router
from .modules.homework.homework_controller import router as homework_router
# from .modules.class.class_controller import router as class_router
import importlib
class_router = importlib.import_module(".modules.class.class_controller", package=__package__).router


# This makes the green lock button appear in Swagger UI
security = HTTPBearer(auto_error=False)

class Tags(str, Enum):
    home = "Home"
    health = "Health Checks"
    users = "User Management"
    items = "Items"

# Database lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to database
    await connect_db()
    yield
    # Shutdown: Disconnect from database
    await disconnect_db()

app = FastAPI(
    title="HK EdTech API",
    version="2.0.0",
    description="Fully automated CI/CD → EC2 → Docker → Nginx → HTTPS ready",
    contact={"name": "Developer: milton chow", "email": "milton@gmail.com"},
    license_info={"name": "MIT"},
    lifespan=lifespan,  # Database lifecycle management
    # This line adds the Authorize button in Swagger/Redoc
    openapi_tags=[
        {"name": "Home", "description": "Protected endpoints"},
        {"name": "Health Checks", "description": "Public"},
        {"name": "User Management"},
        {"name": "Items"},
        {"name": "Profile", "description": "User profile management"},
        {"name": "Scan and Mark / Scan and Upload", "description": "Scan and upload homework"},
    ],
    # This makes the lock appear
    dependencies=[Depends(security)],   # ← important
)

# Configure CORS
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3010")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register module routers
app.include_router(profile_router)
app.include_router(scan_and_upload_router)
app.include_router(class_router)
app.include_router(homework_router)

# PUBLIC ENDPOINTS
@app.get("/health", tags=[Tags.health], include_in_schema=True)
async def health():
    return {"status": "healthy", "service": "fastapi-ec2-prod"}

@app.get("/snowboard", tags=[Tags.health], include_in_schema=True)
async def health():
    return {"status": "healthy", "service": "i-love-snowboard"}

# GLOBAL AUTH MIDDLEWARE (protects everything except the paths below)
@app.middleware("http")
async def supabase_auth_middleware(request: Request, call_next):
    print(f"[AUTH] {request.method} {request.url.path}")

    # ADD skip options to pass the cors checking to the app.add_middleware to check
    if request.method == "OPTIONS":
        print("[AUTH] ✅ Allowing OPTIONS (CORS preflight)")
        return await call_next(request)
    # These paths are always public
    if request.url.path in {"/health", "/openapi.json", "/favicon.ico"} or \
       request.url.path.startswith(("/docs", "/redoc")):
        print(f"[AUTH] ✅ Public path")
        return await call_next(request)

    # Extract Bearer token manually (so your original get_current_user works unchanged)
    auth_header = request.headers.get("Authorization")
    credentials = None
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header[7:].strip()
        credentials = HTTPAuthorizationCredentials(scheme="bearer", credentials=token)
        print(f"[AUTH] 🔑 Token: {token[:30]}...")
    else:
        print("[AUTH] ❌ No Authorization header")

    try:
        user = await get_current_user(credentials)   # ← your original function, untouched
        request.state.user = user
        print(f"[AUTH] ✅ User: {user.get('email', user.get('sub'))}")
    except Exception as e:
        print(f"[AUTH] ❌ Auth failed: {type(e).__name__}: {str(e)}")
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


# OCR test endpoint — Option B flow:
# Backend uses SUPABASE_SERVICE_ROLE_KEY (server-side only) to download the file
# directly from Storage, bypassing RLS. Caller only supplies the bucket + path.
class OcrStoragePathRequest(BaseModel):
    bucket: str
    path: str


@app.post("/ocr/test-from-storage", tags=[Tags.health])
async def test_ocr_from_storage(body: OcrStoragePathRequest):
    supabase_url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not supabase_url or not service_key:
        raise HTTPException(
            status_code=500,
            detail="SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not configured",
        )

    download_url = f"{supabase_url}/storage/v1/object/{body.bucket}/{body.path}"
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(
            download_url,
            headers={
                "Authorization": f"Bearer {service_key}",
                "apikey": service_key,
            },
        )
        if resp.status_code != 200:
            raise HTTPException(
                status_code=resp.status_code,
                detail=f"Failed to download from Supabase Storage: {resp.text}",
            )
        content = resp.content
        content_type = resp.headers.get("content-type", "").lower()

    # Mirror GoogleCloudVisionAPI.detect_document dispatch: PDF vs image by extension,
    # falling back to Content-Type when the path has no extension.
    ext = os.path.splitext(body.path)[1].lower()
    is_pdf = ext == ".pdf" or "pdf" in content_type

    gcv_client = vision.ImageAnnotatorClient()
    if is_pdf:
        return GoogleCloudVisionAPI._detect_pdf(gcv_client, content)
    return GoogleCloudVisionAPI._detect_image(gcv_client, content)

