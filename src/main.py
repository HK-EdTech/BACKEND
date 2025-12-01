from fastapi import FastAPI, Depends
from enum import Enum
from fastapi.routing import APIRoute
from .deps import get_current_user

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
    license_info={
        "name": "MIT",
    },
)

# Health (Anyone can call this)
@app.get("/health", tags=[Tags.health])
def health():
    return {"status": "healthy", "service": "fastapi-ec2-prod"}


# Home - Protecting ALL routes (or just specific ones)
@app.get("/", tags=[Tags.home])
def read_root(user = Depends(get_current_user)):
# def read_root():
    return {"message": "Welcome, authenticated user!"}

# Example CRUD endpoints with perfect colors in Swagger
@app.post("/users", tags=[Tags.users], summary="Create a new user")
def create_user(name: str, email: str):
    return {"id": 42, "name": name, "email": email}

@app.get("/users/{user_id}", tags=[Tags.users], summary="Get user by ID", user = Depends(get_current_user))
def get_user(user_id: int):
    return {"id": user_id, "name": "Milton", "email": "milton@example.com"}

@app.put("/users/{user_id}", tags=[Tags.users], summary="Update user")
def update_user(user_id: int, name: str | None = None):
    return {"id": user_id, "updated": True, "name": name or "unchanged"}

@app.delete("/users/{user_id}", tags=[Tags.users], summary="Delete user")
def delete_user(user_id: int):
    return {"id": user_id, "deleted": True}

# Bonus: Items endpoints (green in Swagger)
@app.post("/items", tags=[Tags.items], summary="Create item")
def create_item(name: str):
    return {"id": 123, "name": name}

@app.get("/items", tags=[Tags.items], summary="List all items")
def list_items():
    return [{"id": 123, "name": "Magic Sword"}]