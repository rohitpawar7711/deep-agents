# Python Code Examples for DeepAgents

This file contains production-grade, reusable Python code patterns that DeepAgents can reference and adapt when generating or refactoring Python code.

---

## Example 1: Robust Data Pipeline Service with Pydantic v2 Validation

```python
"""Data processing service with Pydantic v2 schema validation and custom exceptions."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


# 1. Custom Exception Hierarchy
class ProcessingError(Exception):
    """Base exception for data processing errors."""
    pass


class InvalidRecordError(ProcessingError):
    """Raised when a data record violates business rules."""
    def __init__(self, message: str, record_id: str | None = None) -> None:
        super().__init__(message)
        self.record_id = record_id


# 2. Pydantic v2 Schema
class RecordSchema(BaseModel):
    id: str = Field(..., description="Unique record identifier")
    name: str = Field(..., min_length=2, max_length=100)
    score: float = Field(..., ge=0.0, le=100.0)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Name cannot be empty or whitespace only")
        return cleaned


# 3. Processing Service
@dataclass
class ProcessingResult:
    processed_count: int
    errors: list[str]
    valid_records: list[RecordSchema]


class DataProcessor:
    """Service responsible for validating and transforming batch records."""

    def __init__(self, threshold: float = 50.0) -> None:
        self.threshold = threshold

    def process_batch(self, raw_items: list[dict[str, Any]]) -> ProcessingResult:
        valid_records: list[RecordSchema] = []
        errors: list[str] = []

        for index, item in enumerate(raw_items):
            try:
                record = RecordSchema.model_validate(item)
                if record.score < self.threshold:
                    logger.warning("Record %s dropped: score %.2f below threshold %.2f", record.id, record.score, self.threshold)
                    continue
                valid_records.append(record)
            except Exception as exc:
                err_msg = f"Item at index {index} failed validation: {exc}"
                logger.error(err_msg)
                errors.append(err_msg)

        return ProcessingResult(
            processed_count=len(valid_records),
            errors=errors,
            valid_records=valid_records,
        )
```

---

## Example 2: Resilient Asynchronous API Client with Retry Logic

```python
"""Async API client utilizing httpx with exponential backoff and timeout handling."""

from __future__ import annotations

import asyncio
import logging
from typing import Any
import httpx

logger = logging.getLogger(__name__)


class APIClientError(Exception):
    """Base API client exception."""
    pass


class AsyncResilientClient:
    """Handles async HTTP communication with retries and graceful error recovery."""

    def __init__(
        self,
        base_url: str,
        timeout_seconds: float = 10.0,
        max_retries: int = 3,
        backoff_factor: float = 1.5,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = httpx.Timeout(timeout_seconds)
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> AsyncResilientClient:
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._client:
            await self._client.aclose()

    async def fetch_json(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Client is not initialized. Use 'async with' context manager.")

        attempt = 0
        while attempt < self.max_retries:
            attempt += 1
            try:
                response = await self._client.get(endpoint, params=params)
                response.raise_for_status()
                return response.json()
            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                if attempt >= self.max_retries:
                    logger.error("Failed request to %s after %d attempts: %s", endpoint, attempt, exc)
                    raise APIClientError(f"API request failed after {attempt} attempts") from exc
                
                sleep_time = self.backoff_factor ** attempt
                logger.warning("Attempt %d failed (%s). Retrying in %.2fs...", attempt, exc, sleep_time)
                await asyncio.sleep(sleep_time)

        raise APIClientError("Unexpected loop exit in retry logic")
```

---

## Example 3: Thread-Safe Resource Context Manager

```python
"""Context manager for temporary safe file operations with automatic cleanup."""

from __future__ import annotations

import os
import shutil
import tempfile
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def temporary_workspace(prefix: str = "deepagent_") -> Generator[Path, None, None]:
    """Provide an isolated temporary directory that is guaranteed to be deleted on exit."""
    temp_dir = Path(tempfile.mkdtemp(prefix=prefix))
    try:
        yield temp_dir
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
```

---

## Example 4: Complete Pytest Test Suite

```python
"""Test suite demonstrating fixtures, mocking, and parametrized tests."""

import pytest
from unittest.mock import AsyncMock, patch


# Sample function to test
def calculate_discounted_price(price: float, discount_percent: float) -> float:
    if price < 0:
        raise ValueError("Price cannot be negative")
    if not (0 <= discount_percent <= 100):
        raise ValueError("Discount must be between 0 and 100")
    return round(price * (1 - discount_percent / 100), 2)


# Fixture
@pytest.fixture
def base_price() -> float:
    return 100.0


# Parametrized test
@pytest.mark.parametrize(
    ("discount", "expected"),
    [
        (0.0, 100.0),
        (10.0, 90.0),
        (25.5, 74.5),
        (100.0, 0.0),
    ],
)
def test_calculate_discounted_price_valid(base_price: float, discount: float, expected: float) -> None:
    result = calculate_discounted_price(base_price, discount)
    assert result == expected


@pytest.mark.parametrize("invalid_discount", [-5.0, 105.0])
def test_calculate_discounted_price_invalid_discount(base_price: float, invalid_discount: float) -> None:
    with pytest.raises(ValueError, match="Discount must be between 0 and 100"):
        calculate_discounted_price(base_price, invalid_discount)


def test_calculate_discounted_price_negative_price() -> None:
    with pytest.raises(ValueError, match="Price cannot be negative"):
        calculate_discounted_price(-10.0, 10.0)
```

---

## Example 5: High-Performance Memory-Efficient Generator Pipeline

```python
"""Streaming file processor using generators to process massive files without high memory usage."""

from collections.abc import Generator
from pathlib import Path


def stream_log_lines(file_path: Path) -> Generator[str, None, None]:
    """Yield non-empty stripped lines from a file one at a time."""
    with file_path.open("r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped:
                yield stripped


def filter_errors(lines: Generator[str, None, None]) -> Generator[str, None, None]:
    """Filter stream to only lines containing [ERROR] or [CRITICAL]."""
    for line in lines:
        if "[ERROR]" in line or "[CRITICAL]" in line:
            yield line
```
