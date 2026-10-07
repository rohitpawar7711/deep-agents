---
name: python
description: Professional Python engineering, modern idioms, environment management, packaging, debugging, testing, and performance optimization for DeepAgents. Use whenever writing, analyzing, refactoring, or troubleshooting Python code.
license: MIT
compatibility: Python 3.10+
allowed-tools: read_file write_file edit_file list_directory run_command
---

# Python Engineering Skill

## Overview
This skill provides comprehensive operational guidelines, best practices, and production-tested patterns for writing clean, efficient, maintainable, and robust Python code within DeepAgents workflows.

When handling user queries related to Python development, script execution, module creation, debugging, or optimization, DeepAgents should utilize the standards defined in this skill to ensure high code quality and runtime reliability.

---

## When to Use This Skill
- Writing new Python modules, scripts, or application components.
- Refactoring, modernizing, or debugging existing Python code.
- Designing object-oriented or functional architectures with strict type annotations.
- Setting up virtual environments, package structures, and dependency management.
- Writing unit and integration tests using `pytest`.
- Handling errors gracefully, implementing context managers, and managing resources.
- Profiling and optimizing Python execution speed and memory usage.

---

## Skill Navigation & Progressive Disclosure
For deep, context-specific guidance, consult the companion files in this skill directory:

1. **[`instruction.md`](./instruction.md)**:
   - Detailed step-by-step instructions for Python code organization.
   - Type hints, modern syntax (Python 3.10 - 3.13), and Pydantic v2 data models.
   - Error handling strategies, custom exceptions, and logging standards.
   - Asynchronous programming guidelines (`asyncio`, concurrency, and task management).
   - Package setup, virtual environments (`venv`, uv), and dependency management.
   - DeepAgents-specific coding conventions (read-before-write, localized edits, preserving comments).

2. **[`examples.md`](./examples.md)**:
   - Production-ready reference implementations:
     - Robust data processing service with Pydantic v2 validation.
     - Asynchronous API client with exponential backoff and connection pooling.
     - Resource-safe context managers with automatic cleanup and locking.
     - Complete `pytest` test suite with fixtures, mocks, and parametrization.
     - High-performance streaming data pipelines using generator expressions.

---

## Core Principles for DeepAgents
1. **Read Before Writing**: Always inspect existing files using `read_file` or `list_directory` before modifying or creating new code.
2. **Explicit Over Implicit**: Use descriptive variable names, clear function signatures, and explicit type hints (`typing.Optional`, `typing.Union`, `typing.Annotated`).
3. **Fail Fast & Gracefully**: Validate input early, raise targeted custom exceptions, and provide informative error messages.
4. **Preserve Documentation**: Retain existing docstrings, type comments, and explanatory inline notes when editing code.
5. **Non-Destructive Edits**: Prefer surgical edits using `edit_file` over wiping out and rewriting entire modules.
