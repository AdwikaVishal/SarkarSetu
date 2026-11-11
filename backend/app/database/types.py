"""Database-agnostic column types."""
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import UUID as SQLAlchemyUUID
from sqlalchemy import TypeDecorator, String, Uuid
from sqlalchemy.dialects.postgresql import UUID as PGUUID

if TYPE_CHECKING:
    from sqlalchemy.engine.interfaces import Dialect


class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses PostgreSQL's UUID type when available, otherwise uses a
    CHAR(36) storing as stringified UUID with hyphens.
    """

    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect: "Dialect"):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PGUUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value: uuid.UUID | str | None, dialect: "Dialect") -> str | None:
        if value is None:
            return value
        if dialect.name == "postgresql":
            # PostgreSQL UUID type handles UUID objects natively
            return value
        if isinstance(value, uuid.UUID):
            return str(value)  # This includes hyphens
        # Parse string and return with hyphens
        return str(uuid.UUID(value))

    def process_result_value(self, value: str | None, dialect: "Dialect") -> uuid.UUID | None:
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(value)