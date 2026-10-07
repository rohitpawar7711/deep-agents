# Docker Instructions & Standards for DeepAgents

This document outlines structural rules, optimization strategies, and security requirements for building and managing containerized applications with Docker.

---

## 1. Dockerfile Optimization & Layer Caching

### 1.1 Base Image Selection
- Prefer official `-slim` Debian-based images (e.g., `python:3.11-slim`, `python:3.12-slim`) for general Python and AI applications.
- Avoid full images (e.g., `python:3.11`) in production as they introduce hundreds of megabytes of unnecessary build tools and increased vulnerability surface.
- Avoid Alpine (`python:3.11-alpine`) for Python projects relying on C-extensions (NumPy, PyTorch, Pandas, cryptography) due to `musl` compilation overhead and missing wheels.

### 1.2 Layer Ordering Strategy
Order instructions from least frequently changed to most frequently changed:
1. `FROM base`
2. Environment variables (`ENV`)
3. Working directory (`WORKDIR`)
4. System dependencies (`apt-get update && apt-get install -y --no-install-recommends ...`)
5. Dependency manifest copy (`COPY requirements.txt .` or `pyproject.toml`)
6. Dependency installation (`pip install --no-cache-dir ...`)
7. Application source code copy (`COPY . .`)
8. Execution configuration (`USER`, `EXPOSE`, `ENTRYPOINT`, `CMD`)

---

## 2. Python Container Specifics

Set standard environment variables to optimize Python within containers:
```dockerfile
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
```
- `PYTHONUNBUFFERED=1`: Ensures logs are emitted immediately to standard output without buffering, preventing lost logs during crashes.
- `PYTHONDONTWRITEBYTECODE=1`: Prevents writing `.pyc` files that add image weight without benefit in ephemeral containers.

---

## 3. Multi-Stage Build Architecture

Separate the build/compilation environment from the final execution runtime:
- **Builder Stage**: Installs compiler toolchains (`gcc`, `g++`, `libpq-dev`), builds Python wheels or installs dependencies into a virtual environment.
- **Final Stage**: Copies only the installed virtual environment or built artifacts, omitting compilers, package managers, and temporary files.

Benefits:
- Drastically reduced image size (often by 70–80%).
- Minimal CVE vulnerability attack surface in production.

---

## 4. Security & Hardening Best Practices

### 4.1 Non-Root User
Always create an unprivileged user and group before switching execution context:
```dockerfile
RUN groupadd -r appgroup && useradd -r -g appgroup -u 1001 -s /sbin/nologin appuser
USER appuser
```

### 4.2 Secrets & Credentials
- **Never COPY `.env` or credential files into the image**.
- Always provide `.dockerignore` containing:
  ```
  .env
  .env.*
  *.key
  *.pem
  .git/
  __pycache__/
  .venv/
  ```
- Use Docker secrets or pass environment variables at runtime (`docker run -e KEY=VAL` or `docker compose --env-file`).

---

## 5. Docker Compose Architecture

### 5.1 Service Isolation & Networking
- Define dedicated bridge networks to isolate services.
- Never expose internal database or cache ports to the host machine unless debugging; communicate via internal service DNS names (e.g., `redis:6379`, `postgres:5432`).

### 5.2 Dependency Orchestration with Health Checks
Ensure dependent services wait until their upstream dependencies are truly healthy:
```yaml
services:
  agent-api:
    build: .
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
```

---

## 6. Container Debugging & Health Verification

When troubleshooting containers:
1. **Inspect logs**: `docker logs --tail 100 -f <container_id>`
2. **Execute interactive shell**: `docker exec -it <container_id> /bin/sh` or `/bin/bash`
3. **Inspect exit code & state**: `docker inspect --format='{{.State.ExitCode}} {{.State.Error}}' <container_id>`
4. **Prune dangling resources**: `docker system prune -f`
