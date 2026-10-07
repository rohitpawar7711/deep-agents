# Python Engineering Instructions for DeepAgents

This document provides detailed instructions and standards that DeepAgents must adhere to when developing, editing, debugging, or analyzing Python code.

---

## 1. Code Architecture & Project Organization

### 1.1 Directory Structure
Structure Python projects cleanly with separation of concerns:
```
project_root/
├── src/ (or package_name/)
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── exceptions.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── processor.py
│   └── models/
│       ├── __init__.py
│       └── schemas.py
├── tests/
│   ├── conftest.py
│   ├── test_processor.py
│   └── test_schemas.py
├── pyproject.toml / requirements.txt
├── .env.example
└── README.md
```

### 1.2 Module Design Guidelines
- **Single Responsibility**: Each module, class, and function should do one thing well.
- **Explicit Exports**: Define `__all__ = [...]` in `__init__.py` files to declare public APIs clearly.
- **Circular Imports**: Avoid circular dependencies by extracting common models, types, and interfaces into separate modules (e.g., `types.py` or `models.py`).

---

## 2. Modern Typing & Data Modeling

### 2.1 Python 3.10+ Type Hints
Always use standard modern type annotations:
- Prefer built-in collections: `list[str]`, `dict[str, Any]`, `set[int]`, `tuple[int, ...]` over `typing.List`, `typing.Dict`.
- Use union syntax: `int | float`, `str | None` instead of `Union[int, float]`, `Optional[str]`.
- For structured dictionaries, use `typing.TypedDict` with `total=False` or `NotRequired[...]` for optional keys.
- For immutable data carriers, use `@dataclass(frozen=True)` or `typing.NamedTuple`.

### 2.2 Pydantic v2 Modeling
When handling user inputs, API payloads, or configuration:
- Use `pydantic.BaseModel` with strict type definitions.
- Use `Field(..., description="...", ge=0)` for validation and descriptive metadata.
- Prefer `model_validate()` and `model_dump()` over v1 methods (`parse_obj`, `dict`).
- Use `@field_validator` and `@model_validator(mode='after')` for custom validation.

---

## 3. Error Handling & Robustness

### 3.1 Custom Exception Hierarchies
Never raise generic `Exception` or return error strings directly:
```python
class AppError(Exception):
    """Base application exception."""
    pass

class ValidationError(AppError):
    """Raised when data validation fails."""
    def __init__(self, message: str, field: str | None = None):
        super().__init__(message)
        self.field = field

class ResourceNotFoundError(AppError):
    """Raised when a requested resource is missing."""
    pass
```

### 3.2 Defensive Practices
- **No Bare Except**: Never use `except:` or `except Exception: pass` without logging or explicit handling.
- **Fail Fast**: Check preconditions and raise exceptions early in functions.
- **Context Managers**: Always manage resources (files, sockets, database transactions, locks) with `with` or `async with` statements.
- **Chained Exceptions**: Preserve original context when re-raising with `raise NewException(...) from err`.

---

## 4. Logging & Observability

- Use the standard `logging` module or structured loggers.
- Never use `print()` for diagnostic logging in production modules; reserve `print()` only for CLI output.
- Configure log format with timestamps, log levels, and logger names:
  ```python
  import logging
  logger = logging.getLogger(__name__)
  logger.info("Processing job %s started", job_id)
  ```
- Use `%s` lazy formatting in logger calls rather than f-strings to avoid premature string interpolation overhead when log levels are disabled.

---

## 5. Asynchronous Programming (`asyncio`)

- Use `async`/`await` for I/O-bound operations (network requests, database queries, file streaming).
- Never block the event loop with synchronous calls (e.g., `time.sleep()`, synchronous `requests.get()`); use `asyncio.sleep()` and async HTTP clients like `httpx` or `aiohttp`.
- When running multiple concurrent tasks, prefer `asyncio.TaskGroup` (Python 3.11+) or `asyncio.gather(*tasks, return_exceptions=True)`.
- Always handle cancellation cleanly using `asyncio.CancelledError`.

---

## 6. Testing & Quality Assurance

- **Framework**: Use `pytest` for all unit and integration tests.
- **Fixtures**: Define reusable fixtures in `tests/conftest.py`.
- **Mocking**: Use `unittest.mock.AsyncMock` or `pytest-mock` to isolate external dependencies and API calls.
- **Parametrization**: Test edge cases, empty values, and boundary conditions using `@pytest.mark.parametrize`.
- **Assertion Messages**: Provide informative error messages in assertions when validating complex state.

---

## 7. DeepAgents-Specific Python Conventions

When acting as an autonomous DeepAgent operating on a user's Python codebase:
1. **Inspect Before Changing**: Always read the existing file using `read_file` to understand formatting, style conventions, and dependency constraints before editing.
2. **Targeted Edits**: Use `edit_file` to replace only the specific targeted blocks of code. Do not needlessly rewrite unrelated methods.
3. **Preserve Comments & Docstrings**: Never strip existing comments, docstrings, or license headers unless explicitly requested by the user.
4. **Environment Awareness**: Detect virtual environments (e.g., `.venv`, conda, poetry) before suggesting or executing package installations.
5. **Verify Syntax & Execution**: After modifying a Python file, run a quick syntax or test check via `run_command` (e.g., `python -m py_compile <file>` or `pytest <file>`).
