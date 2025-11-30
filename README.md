# AI Marking Platform

A monorepo for the AI Marking Platform with FastAPI backend and Next.js frontend.

## Project Structure

```
ai-marking-platform/
├── apps/
│   ├── backend/          # FastAPI backend
│   │   ├── src/
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── frontend/         # Next.js frontend
│       ├── app/
│       ├── package.json
│       └── ...
├── packages/             # Shared packages (if needed)
├── ansible/              # Infrastructure as code
├── package.json          # Root workspace config
└── pnpm-workspace.yaml   # pnpm workspace config
```

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Uvicorn** - ASGI server
- **Supabase Auth** - Authentication provider
- **Docker** - Containerization

### Frontend
- **Next.js 16** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **pnpm** - Package manager

### Infrastructure
- **Ansible** - EC2 setup and configuration
- **GitHub Actions** - CI/CD pipeline
- **Nginx** - Reverse proxy
- **Docker** - Container runtime

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- pnpm 10+
- Ansible (for deployment)

### Installation

1. Install dependencies:

```bash
# Install frontend dependencies
pnpm install

# Install backend dependencies
cd apps/backend
pip install -r requirements.txt
```

### Development

Run backend:
```bash
pnpm dev:backend
# or
cd apps/backend
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Run frontend:
```bash
pnpm dev:frontend
# or
cd apps/frontend
pnpm dev
```

### Environment Variables

#### Backend
Create `.env` in `apps/backend/`:
```
DEBUG_TOKEN=super-secret-debug-token
SUPABASE_JWT_SECRET=your-supabase-jwt-secret
SUPABASE_URL=your-supabase-url
```

#### Frontend
Create `.env.local` in `apps/frontend/`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Deployment

### Setting up EC2 dev server
1. Install Ansible locally: `python3 -m pip install --user ansible`
2. Run: `ansible-playbook -i ansible/inventory/hosts.ini ansible/bootstrap_setup_ec2.yaml`

### GitHub Actions
Push to the main branch triggers automatic deployment to EC2.

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## TODO List
- [ ] Add a real domain + free HTTPS: `sudo certbot --nginx -d yourdomain.com`
- [ ] Add health checks + auto-rollback in GitHub Actions
- [ ] Add Prometheus metrics endpoint to FastAPI
- [ ] JWT secret implementation enhancements

## License

MIT
