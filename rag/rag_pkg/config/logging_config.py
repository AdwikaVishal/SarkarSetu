"""Structured logging configuration for the RAG subsystem."""

from __future__ import annotations

import logging
import sys

from rag.config.settings import settings

logger = logging.getLogger("rag")


def configure_logging(level: str | None = None) -> None:
    """Configure structured logging for the RAG subsystem.

    Sensitive values are masked by downstream log helpers; this config
    only sets the level, format, and stream.
    """
    log_level = getattr(logging, (level or settings.log_level).upper(), logging.INFO)

    root = logging.getLogger("rag")
    root.setLevel(log_level)

    # Avoid duplicate handlers if reconfigured
    if root.handlers:
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)

    # Keep propagation off so RAG logs do not double-print via root
    root.propagate = False


def get_logger(name: str) -> logging.Logger:
    """Return a logger scoped to the given module name."""
    return logging.getLogger(f"rag.{name}")


def mask_value(value: str | None) -> str | None:
    """Mask a sensitive value for safe logging."""
    if not value:
        return value
    if len(value) <= 4:
        return "****"
    return f"****{value[-4:]}"
