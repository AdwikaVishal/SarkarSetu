"""Authentication service with JWT and refresh token management."""
from datetime import UTC, datetime, timedelta

from jose import jwt
from jose.exceptions import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_token_type,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.services.password_service import hash_token, password_service


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


class InvalidCredentialsError(AuthenticationError):
    """Raised when credentials are invalid."""
    pass


class AccountInactiveError(AuthenticationError):
    """Raised when account is inactive."""
    pass


class TokenError(AuthenticationError):
    """Raised when token is invalid."""
    pass


class TokenExpiredError(TokenError):
    """Raised when token is expired."""
    pass


class TokenRevokedError(TokenError):
    """Raised when token has been revoked."""
    pass


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def register(
        self,
        email: str,
        full_name: str | None,
        password: str,
    ) -> User:
        """
        Register a new user.

        Args:
            email: User's email address.
            full_name: User's full name.
            password: User's plain text password.

        Returns:
            Created user.

        Raises:
            PasswordPolicyError: If password doesn't meet requirements.
            ValueError: If email already exists.
        """
        # Normalize email
        normalized_email = email.lower().strip()

        # Check for existing user
        existing = await self.db.execute(
            select(User).where(User.email == normalized_email)
        )
        if existing.scalar_one_or_none():
            raise ValueError("Email already registered")

        # Hash password
        hashed_password = password_service.hash_password(password)

        # Create user
        user = User(
            email=normalized_email,
            full_name=full_name,
            hashed_password=hashed_password,
            is_active=True,
            is_verified=False,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def authenticate(
        self,
        email: str,
        password: str,
    ) -> User:
        """
        Authenticate a user with email and password.

        Args:
            email: User's email address.
            password: User's plain text password.

        Returns:
            Authenticated user.

        Raises:
            InvalidCredentialsError: If credentials are invalid.
            AccountInactiveError: If account is inactive.
        """
        normalized_email = email.lower().strip()

        # Get user
        result = await self.db.execute(
            select(User).where(User.email == normalized_email)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise InvalidCredentialsError("Invalid email or password")

        if not user.is_active:
            raise AccountInactiveError("Account is deactivated")

        # Verify password
        if not password_service.verify_password(password, user.hashed_password):
            raise InvalidCredentialsError("Invalid email or password")

        return user

    async def create_tokens(
        self,
        user: User,
    ) -> tuple[str, str]:
        """
        Create access and refresh tokens for a user.

        Args:
            user: User to create tokens for.

        Returns:
            Tuple of (access_token, refresh_token).
        """
        access_token = create_access_token(subject=str(user.id))
        refresh_token = create_refresh_token(subject=str(user.id))

        # Store refresh token hash in database
        refresh_token_hash = hash_token(refresh_token)
        expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)

        db_refresh_token = RefreshToken(
            user_id=user.id,
            token_hash=refresh_token_hash,
            expires_at=expires_at,
            revoked=False,
        )
        self.db.add(db_refresh_token)
        await self.db.commit()

        return access_token, refresh_token

    async def refresh_tokens(
        self,
        refresh_token: str,
    ) -> tuple[str, str]:
        """
        Refresh access and refresh tokens using a valid refresh token.

        Implements token rotation: old refresh token is revoked, new one issued.

        Args:
            refresh_token: Current refresh token.

        Returns:
            Tuple of (new_access_token, new_refresh_token).

        Raises:
            TokenError: If refresh token is invalid, expired, or revoked.
        """
        # Decode and validate token structure
        try:
            payload = decode_token(refresh_token)
        except JWTError as e:
            raise TokenError("Invalid refresh token") from e

        if get_token_type(refresh_token) != TokenType.REFRESH:
            raise TokenError("Invalid token type")

        user_id = payload.get("sub")
        if not user_id:
            raise TokenError("Invalid token payload")

        # Find matching refresh token in database
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked == False,  # noqa: E712
                RefreshToken.expires_at > datetime.now(UTC),
            )
        )
        tokens = result.scalars().all()

        # Find matching token by hash verification
        matching_token = None
        for token in tokens:
            if password_service.verify_password(refresh_token, token.token_hash):
                matching_token = token
                break

        if not matching_token:
            # Check if token was revoked (reuse detection)
            await self._check_revoked_token_reuse(refresh_token, user_id)
            raise TokenError("Invalid or expired refresh token")

        # Revoke old token
        matching_token.revoked = True
        matching_token.revoked_at = datetime.now(UTC)

        # Create new tokens
        user = await self.db.get(User, user_id)
        if not user or not user.is_active:
            raise TokenError("User not found or inactive")

        new_access_token = create_access_token(subject=str(user.id))
        new_refresh_token = create_refresh_token(subject=str(user.id))

        # Store new refresh token
        new_refresh_token_hash = hash_token(new_refresh_token)
        expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)

        new_db_token = RefreshToken(
            user_id=user.id,
            token_hash=new_refresh_token_hash,
            expires_at=expires_at,
            revoked=False,
        )
        self.db.add(new_db_token)
        await self.db.commit()

        return new_access_token, new_refresh_token

    async def _check_revoked_token_reuse(
        self,
        refresh_token: str,
        user_id: str,
    ) -> None:
        """
        Check if a revoked token is being reused (token theft detection).

        Args:
            refresh_token: The refresh token being checked.
            user_id: User ID from token payload.

        Raises:
            TokenRevokedError: If revoked token reuse detected.
        """
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked == True,  # noqa: E712
            )
        )
        revoked_tokens = result.scalars().all()

        for token in revoked_tokens:
            if password_service.verify_password(refresh_token, token.token_hash):
                # Token reuse detected - revoke all tokens for this user
                await self.revoke_all_user_tokens(user_id)
                raise TokenRevokedError("Token reuse detected - all sessions revoked")

    async def logout(self, refresh_token: str) -> None:
        """
        Revoke a refresh token (logout).

        Args:
            refresh_token: Refresh token to revoke.
        """
        try:
            payload = decode_token(refresh_token)
        except JWTError:
            # If token is invalid, we can't identify it - safe no-op
            return

        if get_token_type(refresh_token) != TokenType.REFRESH:
            return

        user_id = payload.get("sub")
        if not user_id:
            return

        # Find and revoke matching token
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked == False,  # noqa: E712
            )
        )
        tokens = result.scalars().all()

        for token in tokens:
            if password_service.verify_password(refresh_token, token.token_hash):
                token.revoked = True
                token.revoked_at = datetime.now(UTC)
                await self.db.commit()
                break

    async def revoke_all_user_tokens(self, user_id: str) -> None:
        """
        Revoke all refresh tokens for a user.

        Args:
            user_id: User ID to revoke tokens for.
        """
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked == False,  # noqa: E712
            )
        )
        tokens = result.scalars().all()

        for token in tokens:
            token.revoked = True
            token.revoked_at = datetime.now(UTC)

        if tokens:
            await self.db.commit()

    async def get_current_user(self, token: str) -> User:
        """
        Get current user from access token.

        Args:
            token: Access token.

        Returns:
            Authenticated user.

        Raises:
            TokenError: If token is invalid.
            TokenExpiredError: If token is expired.
        """
        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError as e:  # type: ignore[attr-defined]
            raise TokenExpiredError("Access token has expired") from e
        except JWTError as e:
            raise TokenError("Invalid access token") from e

        if get_token_type(token) != TokenType.ACCESS:
            raise TokenError("Invalid token type")

        user_id = payload.get("sub")
        if not user_id:
            raise TokenError("Invalid token payload")

        user = await self.db.get(User, user_id)
        if not user:
            raise TokenError("User not found")

        if not user.is_active:
            raise AccountInactiveError("Account is deactivated")

        return user
