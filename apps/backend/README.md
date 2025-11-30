# Backend - FastAPI

AI Marking Platform backend API built with FastAPI.

## Features

- FastAPI REST API
- Authentication with Supabase JWT
- Debug token support for development
- Docker support

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run development server:
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## Environment Variables

- `DEBUG_TOKEN`: Debug token for development (default: "super-secret-debug-token")
- `SUPABASE_JWT_SECRET`: Supabase JWT secret for production
- `SUPABASE_URL`: Supabase project URL

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
