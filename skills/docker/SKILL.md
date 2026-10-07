---
name: docker
description: Containerization, Dockerfile optimization, multi-stage builds, caching, security hardening, docker-compose orchestration, and container troubleshooting for DeepAgents. Use whenever containerizing applications, configuring microservices, optimizing build performance, or debugging containers.
license: MIT
compatibility: Docker Engine >= 20.10, Docker Compose v2+
allowed-tools: read_file write_file edit_file list_directory run_command
---

# Docker & Containerization Skill

## Overview
This skill provides comprehensive operational guidelines, best practices, and production-tested templates for containerizing applications, writing optimized Dockerfiles, managing multi-container stacks with Docker Compose, and securing containerized environments for DeepAgents and AI workflows.

When handling user queries about containerization, Docker packaging, dependency isolation, environment parity, or deployment setups, DeepAgents should apply the patterns defined in this skill.

---

## When to Use This Skill
- Creating or optimizing `Dockerfile` configurations for Python, AI, or web services.
- Implementing multi-stage builds to minimize image size and eliminate build tools from runtime.
- Orchestrating multi-container services (databases, vector stores, Redis, LLM microservices) via `docker-compose.yml`.
- Writing robust `.dockerignore` files to prevent secret leakage and cache invalidation.
- Hardening container security: running as non-root, read-only root filesystems, and avoiding privilege escalation.
- Debugging container startup crashes, failed builds, network issues, or port mapping errors.

---

## Skill Navigation & Progressive Disclosure
For deep, context-specific guidance, consult the companion files in this skill directory:

1. **[`instruction.md`](./instruction.md)**:
   - Dockerfile construction rules: base image selection, layer ordering, and caching efficiency.
   - Python-specific container optimizations: wheels, pip cache mounts, bytecode, and unbuffered I/O.
   - Security hardening: non-root users, secret handling, and permission boundaries.
   - Docker Compose architecture: networks, healthchecks, restart policies, and dependency conditions (`service_healthy`).
   - Debugging recipes and inspection techniques (`docker logs`, `docker exec`, resource limits).

2. **[`examples.md`](./examples.md)**:
   - Production-ready reference implementations:
     - Multi-stage `Dockerfile` for high-performance Python/FastAPI/DeepAgents services.
     - Production-ready `docker-compose.yml` stack with Redis, PostgreSQL, and Agent API.
     - Comprehensive `.dockerignore` template.
     - Development Dockerfile with live volume mounting and hot reload.
     - Health check scripts and container entrypoint scripts.

---

## Core Containerization Principles
1. **Minimize Image Footprint**: Use slim or alpine base images (e.g., `python:3.11-slim`), leverage multi-stage builds, and remove temporary build artifacts in the same layer.
2. **Maximize Build Cache**: Place infrequently changing directives (`FROM`, `WORKDIR`, OS package installations) at the top, and frequently changing code at the bottom.
3. **Never Run as Root in Production**: Create and switch to a dedicated unprivileged user (`USER appuser`).
4. **Never Bake Secrets Into Images**: Never include API keys, credentials, or `.env` files in images; inject them via environment variables or secret mounts at runtime.
5. **Always Implement Health Checks**: Provide explicit health checks to enable orchestration systems to detect unresponsive services.
