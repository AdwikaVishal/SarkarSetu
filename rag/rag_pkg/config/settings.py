"""Runtime configuration for the RAG/document-intelligence subsystem.

All settings are loaded from environment variables via pydantic-settings
with sensible defaults. Secrets are never hardcoded.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="RAG_",
    )

    # Directories
    rag_data_dir: Path = Field(default=Path("rag/data"), description="RAG data root")
    rag_raw_dir: Path = Field(default=Path("rag/data/raw"), description="Raw source documents")
    rag_processed_dir: Path = Field(
        default=Path("rag/data/processed"), description="Processed chunk store"
    )
    rag_metadata_dir: Path = Field(
        default=Path("rag/data/metadata"), description="Source metadata store"
    )
    rag_indexes_dir: Path = Field(
        default=Path("rag/data/indexes"), description="FAISS index store"
    )

    # Embedding model
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Sentence-Transformers model name",
    )
    embedding_dim: int = Field(default=384, description="Embedding vector dimension")

    # Chunking
    chunk_target_tokens: int = Field(
        default=600, description="Target chunk size in tokens"
    )
    chunk_overlap_tokens: int = Field(
        default=100, description="Chunk overlap in tokens"
    )

    # Retrieval
    default_top_k: int = Field(default=5, description="Default top-k retrieval")
    min_similarity_score: float = Field(
        default=0.30, description="Minimum similarity score to consider a hit"
    )

    # Index persistence
    faiss_index_path: Path = Field(
        default=Path("rag/data/indexes/knowledge_base.index"),
        description="Persistent FAISS index path",
    )
    metadata_store_path: Path = Field(
        default=Path("rag/data/metadata/chunks.jsonl"),
        description="Chunk metadata store path",
    )
    source_registry_path: Path = Field(
        default=Path("rag/data/metadata/source_registry.jsonl"),
        description="Source registry path",
    )

    # File validation
    max_file_size_mb: int = Field(default=50, description="Max upload file size in MB")
    allowed_extensions_csv: str = Field(
        default=".pdf", description="Comma-separated allowed file extensions"
    )

    # OCR
    tesseract_cmd: str | None = Field(
        default=None, description="Path to tesseract executable (auto-detect if None)"
    )
    ocr_min_text_chars: int = Field(
        default=50, description="Minimum extractable chars before OCR fallback"
    )

    # Security / privacy
    mask_sensitive_in_logs: bool = Field(
        default=True, description="Mask sensitive values in log output"
    )

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")


settings = Settings()

_ALLOWED_EXTENSIONS_CACHE: set[str] | None = None


def allowed_extensions() -> set[str]:
    """Return the set of allowed file extensions (lowercase, with dot)."""
    global _ALLOWED_EXTENSIONS_CACHE
    if _ALLOWED_EXTENSIONS_CACHE is None:
        _ALLOWED_EXTENSIONS_CACHE = {
            ext.strip().lower()
            for ext in settings.allowed_extensions_csv.split(",")
            if ext.strip()
        }
    return _ALLOWED_EXTENSIONS_CACHE


def ensure_directories() -> None:
    """Create all configured directories if they do not exist."""
    for directory in (
        settings.rag_data_dir,
        settings.rag_raw_dir,
        settings.rag_processed_dir,
        settings.rag_metadata_dir,
        settings.rag_indexes_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)
