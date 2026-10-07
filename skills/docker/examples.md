# Docker Configuration Examples for DeepAgents

This file provides production-tested, reusable Docker configuration files and patterns.

---

## Example 1: Production Multi-Stage `Dockerfile` for Python / DeepAgents App

```dockerfile
# ==========================================
# Stage 1: Build Environment & Wheels
# ==========================================
FROM python:3.11-slim AS builder

WORKDIR /build

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Install temporary build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create dedicated virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install application dependencies
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# ==========================================
# Stage 2: Final Minimal Runtime Image
# ==========================================
FROM python:3.11-slim AS runner

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

# Install only essential runtime libraries (e.g., libpq for PostgreSQL)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-built virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Create unprivileged application user
RUN groupadd -r appgroup && useradd -r -g appgroup -u 10001 -s /sbin/nologin appuser

# Copy application source code
COPY --chown=appuser:appgroup . .

# Switch to unprivileged user
USER appuser

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Example 2: Comprehensive `.dockerignore` Template

```gitignore
# Git & VCS
.git/
.gitignore
.gitattributes

# Environment & Credentials (NEVER BAKE SECRETS)
.env
.env.*
*.pem
*.key
*.crt
id_rsa*

# Python caches & virtual environments
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.venv/
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Testing & Linting artifacts
.pytest_cache/
.coverage
htmlcov/
.tox/
.mypy_cache/
.ruff_cache/

# IDE & OS files
.DS_Store
.idea/
.vscode/
*.swp
*.swo

# Docker and local logs
Dockerfile*
docker-compose*.yml
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
```

---

## Example 3: Full-Stack Multi-Service `docker-compose.yml`

```yaml
version: "3.8"

services:
  # Primary DeepAgents / FastAPI Service
  agent-api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: deepagent_api
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=postgresql://agent_user:${DB_PASSWORD}@postgres:5432/agent_db
    depends_on:
      redis:
        condition: service_healthy
      postgres:
        condition: service_healthy
    networks:
      - agent_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 15s
      timeout: 5s
      retries: 3
      start_period: 10s

  # Redis for Agent Checkpointing / Cache
  redis:
    image: redis:7-alpine
    container_name: deepagent_redis
    restart: unless-stopped
    command: ["redis-server", "--appendonly", "yes"]
    volumes:
      - redis_data:/data
    networks:
      - agent_network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  # PostgreSQL for Persistent LangGraph Store
  postgres:
    image: postgres:16-alpine
    container_name: deepagent_postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: agent_user
      POSTGRES_PASSWORD: ${DB_PASSWORD:-supersecretpassword}
      POSTGRES_DB: agent_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - agent_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U agent_user -d agent_db"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  redis_data:
  postgres_data:

networks:
  agent_network:
    driver: bridge
```

---

## Example 4: Development `docker-compose.override.yml` (Hot Reload)

```yaml
version: "3.8"

services:
  agent-api:
    build:
      context: .
      dockerfile: Dockerfile
      target: builder # Use builder stage for dev tools
    volumes:
      - .:/app # Mount local code for hot reloading
    environment:
      - DEBUG=True
    command: ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

---

## Example 5: Robust Container Entrypoint Script (`entrypoint.sh`)

```bash
#!/bin/sh
set -e

echo "[Entrypoint] Verifying database connectivity..."
while ! nc -z postgres 5432; do
  echo "Waiting for PostgreSQL to accept connections..."
  sleep 1
done
echo "[Entrypoint] Database is reachable."

# Run database migrations if necessary
echo "[Entrypoint] Running database migrations..."
python -m alembic upgrade head || echo "No migrations found, proceeding..."

# Execute the primary CMD passed to docker container
echo "[Entrypoint] Starting application process: $@"
exec "$@"
```
