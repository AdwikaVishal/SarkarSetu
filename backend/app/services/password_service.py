"""Password security service using Argon2id."""
import re
import secrets

import argon2
from argon2 import PasswordHasher

from app.core.config import settings


class PasswordPolicyError(ValueError):
    """Raised when password doesn't meet policy requirements."""
    pass


class PasswordService:
    """Service for secure password hashing and verification using Argon2id."""

    def __init__(self) -> None:
        self._hasher = PasswordHasher(
            time_cost=settings.argon2_time_cost,
            memory_cost=settings.argon2_memory_cost,
            parallelism=settings.argon2_parallelism,
            hash_len=settings.argon2_hash_length,
            salt_len=settings.argon2_salt_length,
            type=argon2.Type.ID,
        )
        self._policy_regex = self._build_policy_regex()

    def _build_policy_regex(self) -> re.Pattern | None:
        """Build regex pattern for password policy validation."""
        parts = []
        if settings.require_uppercase:
            parts.append(r"(?=.*[A-Z])")
        if settings.require_lowercase:
            parts.append(r"(?=.*[a-z])")
        if settings.require_digits:
            parts.append(r"(?=.*\d)")
        if settings.require_special_chars:
            parts.append(r"(?=.*[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?])")
        if not parts:
            return None
        pattern = "^" + "".join(parts) + f".{{{settings.min_password_length},}}$"
        return re.compile(pattern)

    def validate_password(self, password: str) -> None:
        """
        Validate password against policy requirements.

        Args:
            password: Plain text password to validate.

        Raises:
            PasswordPolicyError: If password doesn't meet requirements.
        """
        if not password:
            raise PasswordPolicyError("Password cannot be empty")

        if len(password) < settings.min_password_length:
            raise PasswordPolicyError(
                f"Password must be at least {settings.min_password_length} characters long"
            )

        if self._policy_regex and not self._policy_regex.match(password):
            requirements = []
            if settings.require_uppercase:
                requirements.append("one uppercase letter")
            if settings.require_lowercase:
                requirements.append("one lowercase letter")
            if settings.require_digits:
                requirements.append("one digit")
            if settings.require_special_chars:
                requirements.append("one special character")
            raise PasswordPolicyError(
                f"Password must contain {', '.join(requirements)}"
            )

    def hash_password(self, password: str) -> str:
        """
        Hash a plain text password using Argon2id.

        Args:
            password: Plain text password to hash.

        Returns:
            Argon2id hash string.
        """
        self.validate_password(password)
        return self._hasher.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain text password against an Argon2id hash.

        Args:
            plain_password: Plain text password to verify.
            hashed_password: Argon2id hash to verify against.

        Returns:
            True if password matches, False otherwise.
        """
        if not plain_password or not hashed_password:
            return False
        try:
            return self._hasher.verify(hashed_password, plain_password)
        except argon2.exceptions.VerifyMismatchError:
            return False
        except argon2.exceptions.InvalidHashError:
            return False

    def needs_rehash(self, hashed_password: str) -> bool:
        """
        Check if a hash needs rehashing due to parameter changes.

        Args:
            hashed_password: Existing Argon2id hash.

        Returns:
            True if rehash is needed, False otherwise.
        """
        try:
            return self._hasher.check_needs_rehash(hashed_password)
        except argon2.exceptions.InvalidHashError:
            return True


password_service = PasswordService()


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token.

    Args:
        length: Length of the token in bytes.

    Returns:
        URL-safe base64 encoded token string.
    """
    return secrets.token_urlsafe(length)


def hash_token(token: str) -> str:
    """
    Hash a token using Argon2id for storage.

    Args:
        token: Raw token to hash.

    Returns:
        Argon2id hash of the token.
    """
    return password_service.hash_password(token)
