# Deployment Guide

## Prerequisites

- Python 3.10+
- Node.js 18+ 
- PostgreSQL 14+
- npm or yarn

## Local Development Setup

### 1. Database Setup

```bash
# Create PostgreSQL database
createdb pstl_dev
```

### 2. Backend Setup

```bash
# Navigate to project root
cd public-subsidy-transparency-ledger

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > backend/.env << EOF
DATABASE_URL=postgresql://postgres:password@localhost:5432/pstl_dev
SECRET_KEY=your-secret-key-min-32-chars-long-here
ENVIRONMENT=development
EOF

# Run the backend
cd backend
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

### 3. Seed Database (Development Only)

```bash
python -m backend.seed.seed_data
```

This creates ~200 subsidies, projects, and disbursements with realistic data.

### 4. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `SECRET_KEY` | JWT signing key (min 32 chars in production) | Yes |
| `ENVIRONMENT` | "development" or "production" | No |
| `JWT_ALGORITHM` | JWT algorithm (default: HS256) | No |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry (default: 60) | No |
| `ALLOW_ORIGINS` | CORS origins (comma-separated) | No |
| `BLOCKCHAIN_RPC` | Blockchain RPC URL (optional) | No |

## Production Deployment

### Backend

```bash
# Set production environment variables
export DATABASE_URL=postgresql://user:pass@host:5432/pstl_prod
export SECRET_KEY=<strong-secret-key>
export ENVIRONMENT=production

# Run with production settings
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Frontend

```bash
cd frontend
npm run build
# Serve the dist/ folder with nginx or similar
```

### Docker (Optional)

```bash
docker-compose -f devops/docker-compose.yml up -d
```

## Default Users

After running the seed script, the following users are available:

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | Admin |
| auditor | auditor123 | Auditor |
| official | official123 | Government Official |
| media | media123 | Media |

## Verification

```bash
# Check API health
curl http://localhost:8000/health

# Check API docs
curl http://localhost:8000/docs
```
