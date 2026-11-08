"""Authentication and authorization tests."""
from datetime import timedelta
from uuid import uuid4

import pytest

from app.core.security import TokenType, create_access_token, create_refresh_token
from app.services.auth_service import (
    AccountInactiveError,
    AuthService,
    InvalidCredentialsError,
    TokenError,
    TokenExpiredError,
    TokenRevokedError,
)
from app.services.password_service import PasswordPolicyError, password_service


# Test Registration
class TestRegistration:
    """Tests for user registration."""

    @pytest.mark.asyncio
    async def test_successful_registration(self, db_session):
        """Test successful user registration."""
        auth_service = AuthService(db_session)

        user = await auth_service.register(
            email="test@example.com",
            full_name="Test User",
            password="StrongPassword123!",
        )

        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.is_active is True
        assert user.is_verified is False
        assert user.hashed_password != "StrongPassword123!"

    @pytest.mark.asyncio
    async def test_duplicate_email_rejection(self, db_session):
        """Test that duplicate email is rejected."""
        auth_service = AuthService(db_session)

        await auth_service.register(
            email="duplicate@example.com",
            full_name="User One",
            password="StrongPassword123!",
        )

        with pytest.raises(ValueError, match="Email already registered"):
            await auth_service.register(
                email="duplicate@example.com",
                full_name="User Two",
                password="AnotherPassword123!",
            )

    @pytest.mark.asyncio
    async def test_invalid_email_rejection(self, db_session):
        """Test that invalid email format is rejected by Pydantic schema."""
        # This is tested at the API level via schema validation
        # The service doesn't validate email format, the schema does
        auth_service = AuthService(db_session)
        # Service-level just normalizes email
        user = await auth_service.register(
            email="  TEST@EXAMPLE.COM  ",
            full_name="Test User",
            password="StrongPassword123!",
        )
        assert user.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_password_hash_differs_from_plaintext(self, db_session):
        """Test that password hash is not the plaintext password."""
        auth_service = AuthService(db_session)

        user = await auth_service.register(
            email="hash@example.com",
            full_name="Hash User",
            password="StrongPassword123!",
        )

        assert user.hashed_password != "StrongPassword123!"
        assert user.hashed_password.startswith("$argon2id$")

    @pytest.mark.asyncio
    async def test_weak_password_rejection(self, db_session):
        """Test that weak passwords are rejected."""
        AuthService(db_session)

        weak_passwords = [
            "short",  # too short
            "nouppercase123!",  # no uppercase
            "NOLOWERCASE123!",  # no lowercase
            "NoDigits!",  # no digits
            "NoSpecialChars123",  # no special chars
        ]

        for weak_pwd in weak_passwords:
            with pytest.raises(PasswordPolicyError):
                password_service.validate_password(weak_pwd)


# Test Login
class TestLogin:
    """Tests for user login."""

    @pytest.mark.asyncio
    async def test_correct_credentials(self, db_session):
        """Test login with correct credentials."""
        auth_service = AuthService(db_session)

        await auth_service.register(
            email="login@example.com",
            full_name="Login User",
            password="StrongPassword123!",
        )

        user = await auth_service.authenticate(
            email="login@example.com",
            password="StrongPassword123!",
        )

        assert user.email == "login@example.com"
        assert user.full_name == "Login User"

    @pytest.mark.asyncio
    async def test_incorrect_password(self, db_session):
        """Test login with incorrect password."""
        auth_service = AuthService(db_session)

        await auth_service.register(
            email="wrongpass@example.com",
            full_name="Wrong Pass User",
            password="StrongPassword123!",
        )

        with pytest.raises(InvalidCredentialsError):
            await auth_service.authenticate(
                email="wrongpass@example.com",
                password="WrongPassword123!",
            )

    @pytest.mark.asyncio
    async def test_nonexistent_user(self, db_session):
        """Test login with nonexistent user."""
        auth_service = AuthService(db_session)

        with pytest.raises(InvalidCredentialsError):
            await auth_service.authenticate(
                email="nonexistent@example.com",
                password="StrongPassword123!",
            )

    @pytest.mark.asyncio
    async def test_inactive_user(self, db_session):
        """Test login with inactive account."""
        auth_service = AuthService(db_session)

        user = await auth_service.register(
            email="inactive@example.com",
            full_name="Inactive User",
            password="StrongPassword123!",
        )

        # Deactivate user
        user.is_active = False
        await db_session.commit()

        with pytest.raises(AccountInactiveError):
            await auth_service.authenticate(
                email="inactive@example.com",
                password="StrongPassword123!",
            )

    @pytest.mark.asyncio
    async def test_token_generation(self, db_session):
        """Test that tokens are generated on login."""
        auth_service = AuthService(db_session)

        user = await auth_service.register(
            email="tokengen@example.com",
            full_name="Token Gen User",
            password="StrongPassword123!",
        )

        authenticated_user = await auth_service.authenticate(
            email="tokengen@example.com",
            password="StrongPassword123!",
        )

        access_token, refresh_token = await auth_service.create_tokens(authenticated_user)

        assert access_token is not None
        assert refresh_token is not None
        assert len(access_token) > 0
        assert len(refresh_token) > 0

        # Verify token structure
        from app.core.security import decode_token, get_token_type
        access_payload = decode_token(access_token)
        refresh_payload = decode_token(refresh_token)

        assert access_payload["sub"] == str(user.id)
        assert get_token_type(access_token) == TokenType.ACCESS
        assert refresh_payload["sub"] == str(user.id)
        assert get_token_type(refresh_token) == TokenType.REFRESH


# Test JWT
class TestJWT:
    """Tests for JWT token handling."""

    @pytest.mark.asyncio
    async def test_valid_access_token(self, db_session):
        """Test valid access token authentication."""
        auth_service = AuthService(db_session)

        user = await auth_service.register(
            email="jwttest@example.com",
            full_name="JWT User",
            password="StrongPassword123!",
        )

        access_token, _ = await auth_service.create_tokens(user)
        authenticated_user = await auth_service.get_current_user(access_token)

        assert authenticated_user.id == user.id

    @pytest.mark.asyncio
    async def test_expired_access_token(self, db_session):
        """Test expired access token rejection."""
        auth_service = AuthService(db_session)

        user = await auth_service.register(
            email="expired@example.com",
            full_name="Expired User",
            password="StrongPassword123!",
        )

        # Create token with negative expiration
        expired_token = create_access_token(
            subject=str(user.id),
            expires_delta=timedelta(seconds=-1),
        )

        with pytest.raises(TokenExpiredError):
            await auth_service.get_current_user(expired_token)

    @pytest.mark.asyncio
    async def test_invalid_signature(self, db_session):
        """Test token with invalid signature rejection."""
        auth_service = AuthService(db_session)

        user = await auth_service.register(
            email="invalidsig@example.com",
            full_name="Invalid Sig User",
            password="StrongPassword123!",
        )

        # Create token with wrong secret
        from jose import jwt

        from app.core.config import settings
        invalid_token = jwt.encode(
            {"sub": str(user.id), "type": "access"},
            "wrong-secret",
            algorithm=settings.jwt_algorithm,
        )

        with pytest.raises(TokenError):
            await auth_service.get_current_user(invalid_token)

    @pytest.mark.asyncio
    async def test_invalid_token_type(self, db_session):
        """Test refresh token used as access token rejection."""
        auth_service = AuthService(db_session)

        user = await auth_service.register(
            email="tokentype@example.com",
            full_name="Token Type User",
            password="StrongPassword123!",
        )

        _, refresh_token = await auth_service.create_tokens(user)

        with pytest.raises(TokenError, match="Invalid token type"):
            await auth_service.get_current_user(refresh_token)

    @pytest.mark.asyncio
    async def test_missing_authorization(self, db_session):
        """Test that missing authorization is handled."""
        auth_service = AuthService(db_session)

        with pytest.raises(TokenError):
            await auth_service.get_current_user("")

    @pytest.mark.asyncio
    async def test_invalid_user_subject(self, db_session):
        """Test token with non-existent user ID."""
        auth_service = AuthService(db_session)

        invalid_token = create_access_token(subject=str(uuid4()))

        with pytest.raises(TokenError, match="User not found"):
            await auth_service.get_current_user(invalid_token)


# Test Refresh Tokens
class TestRefreshTokens:
    """Tests for refresh token rotation."""

    @pytest.mark.asyncio
    async def test_successful_refresh(self, db_session):
        """Test successful token refresh."""
        auth_service = AuthService(db_session)

        user = await auth_service.register(
            email="refresh@example.com",
            full_name="Refresh User",
            password="StrongPassword123!",
        )

        _, refresh_token = await auth_service.create_tokens(user)
        new_access, new_refresh = await auth_service.refresh_tokens(refresh_token)

        assert new_access != ""
        assert new_refresh != ""
        assert new_access != refresh_token

    @pytest.mark.asyncio
    async def test_old_token_invalid_after_rotation(self, db_session):
        """Test that old refresh token is invalid after rotation."""
        auth_service = AuthService(db_session)

        user = await auth_service.register(
            email="rotation@example.com",
            full_name="Rotation User",
            password="StrongPassword123!",
        )

        _, refresh_token = await auth_service.create_tokens(user)
        await auth_service.refresh_tokens(refresh_token)

        # Old token should now be invalid (revoked and reuse detected)
        with pytest.raises(TokenRevokedError):
            await auth_service.refresh_tokens(refresh_token)

    @pytest.mark.asyncio
    async def test_expired_refresh_token_rejection(self, db_session):
        """Test expired refresh token rejection."""
        auth_service = AuthService(db_session)

        user = await auth_service.register(
            email="refreshexpired@example.com",
            full_name="Refresh Expired User",
            password="StrongPassword123!",
        )

        # Create refresh token with negative expiration
        expired_refresh = create_refresh_token(
            subject=str(user.id),
            expires_delta=timedelta(seconds=-1),
        )

        # Store expired token in DB
        from datetime import UTC, datetime

        from app.models.refresh_token import RefreshToken
        from app.services.password_service import hash_token

        expired_hash = hash_token(expired_refresh)
        expired_token = RefreshToken(
            user_id=user.id,
            token_hash=expired_hash,
            expires_at=datetime.now(UTC) - timedelta(hours=1),
            revoked=False,
        )
        db_session.add(expired_token)
        await db_session.commit()

        with pytest.raises(TokenError):
            await auth_service.refresh_tokens(expired_refresh)

    @pytest.mark.asyncio
    async def test_revoked_refresh_token_rejection(self, db_session):
        """Test revoked refresh token rejection."""
        auth_service = AuthService(db_session)

        user = await auth_service.register(
            email="revoked@example.com",
            full_name="Revoked User",
            password="StrongPassword123!",
        )

        _, refresh_token = await auth_service.create_tokens(user)
        await auth_service.logout(refresh_token)

        with pytest.raises(TokenError):
            await auth_service.refresh_tokens(refresh_token)

    @pytest.mark.asyncio
    async def test_refresh_token_reuse_detection(self, db_session):
        """Test refresh token reuse detection and family revocation."""
        auth_service = AuthService(db_session)

        user = await auth_service.register(
            email="reuse@example.com",
            full_name="Reuse User",
            password="StrongPassword123!",
        )

        _, refresh_token = await auth_service.create_tokens(user)
        # First rotation
        _, new_refresh = await auth_service.refresh_tokens(refresh_token)
        # Try to use the old token again (theft simulation)
        with pytest.raises(TokenRevokedError):
            await auth_service.refresh_tokens(refresh_token)

        # New token should also be revoked (family revoked)
        with pytest.raises(TokenRevokedError):
            await auth_service.refresh_tokens(new_refresh)


# Test Logout
class TestLogout:
    """Tests for logout functionality."""

    @pytest.mark.asyncio
    async def test_logout_revokes_token(self, db_session):
        """Test that logout revokes the refresh token."""
        auth_service = AuthService(db_session)

        user = await auth_service.register(
            email="logout@example.com",
            full_name="Logout User",
            password="StrongPassword123!",
        )

        _, refresh_token = await auth_service.create_tokens(user)
        await auth_service.logout(refresh_token)

        # Token should now be invalid
        with pytest.raises(TokenError):
            await auth_service.refresh_tokens(refresh_token)

    @pytest.mark.asyncio
    async def test_repeated_logout_safe(self, db_session):
        """Test that repeated logout requests are safe."""
        auth_service = AuthService(db_session)

        user = await auth_service.register(
            email="repeatedlogout@example.com",
            full_name="Repeated Logout User",
            password="StrongPassword123!",
        )

        _, refresh_token = await auth_service.create_tokens(user)
        await auth_service.logout(refresh_token)
        await auth_service.logout(refresh_token)  # Should not raise

        # Should be safe to call multiple times
        assert True


# Test Ownership
class TestOwnershipAuthorization:
    """Tests for ownership authorization."""

    @pytest.mark.asyncio
    async def test_user_a_cannot_access_user_b_business_profile(self, db_session):
        """Test User A cannot access User B's business profile."""
        from app.services.ownership import OwnershipService, ResourceNotFoundError

        auth_service = AuthService(db_session)

        user_a = await auth_service.register(
            email="usera@example.com",
            full_name="User A",
            password="StrongPassword123!",
        )
        user_b = await auth_service.register(
            email="userb@example.com",
            full_name="User B",
            password="StrongPassword123!",
        )

        # User B creates a business profile
        await auth_service.register(
            email="userb_profile@example.com",
            full_name="User B Profile",
            password="StrongPassword123!",
        )
        # Wait, we need to create a business profile through the proper service
        from app.models.business import BusinessProfile
        profile = BusinessProfile(
            user_id=user_b.id,
            business_name="User B Business",
            business_type="Manufacturing",
            industry="Textiles",
            state="Maharashtra",
            district="Mumbai",
            business_structure="Private Limited",
            business_stage="Growth",
        )
        db_session.add(profile)
        await db_session.commit()
        await db_session.refresh(profile)

        ownership_service = OwnershipService(db_session)

        # User A tries to access User B's business profile
        with pytest.raises(ResourceNotFoundError):
            await ownership_service.get_user_business_profile(user_a.id, profile.id)

    @pytest.mark.asyncio
    async def test_user_a_cannot_access_user_b_conversations(self, db_session):
        """Test User A cannot access User B's conversations."""
        from app.models.conversation import Conversation
        from app.services.ownership import OwnershipService, ResourceNotFoundError

        auth_service = AuthService(db_session)

        user_a = await auth_service.register(
            email="usera2@example.com",
            full_name="User A2",
            password="StrongPassword123!",
        )
        user_b = await auth_service.register(
            email="userb2@example.com",
            full_name="User B2",
            password="StrongPassword123!",
        )

        # User B creates a conversation
        conv = Conversation(
            user_id=user_b.id,
            title="User B Conversation",
        )
        db_session.add(conv)
        await db_session.commit()
        await db_session.refresh(conv)

        ownership_service = OwnershipService(db_session)

        with pytest.raises(ResourceNotFoundError):
            await ownership_service.get_user_conversation(user_a.id, conv.id)

    @pytest.mark.asyncio
    async def test_user_a_cannot_access_user_b_recommendations(self, db_session):
        """Test User A cannot access User B's recommendations."""
        from app.models.business import BusinessProfile
        from app.models.recommendation import Recommendation
        from app.services.ownership import OwnershipService, ResourceNotFoundError
        auth_service = AuthService(db_session)

        user_a = await auth_service.register(
            email="usera3@example.com",
            full_name="User A3",
            password="StrongPassword123!",
        )
        user_b = await auth_service.register(
            email="userb3@example.com",
            full_name="User B3",
            password="StrongPassword123!",
        )

        # Create business profile for user_b
        profile_b = BusinessProfile(
            user_id=user_b.id,
            business_name="User B Business",
            business_type="Manufacturing",
            industry="Textiles",
            state="Maharashtra",
            district="Mumbai",
            business_structure="Private Limited",
            business_stage="Growth",
        )
        db_session.add(profile_b)
        await db_session.commit()
        await db_session.refresh(profile_b)

        rec = Recommendation(
            user_id=user_b.id,
            business_profile_id=profile_b.id,
            category="Test",
            title="Test Rec",
            description="Test",
        )
        db_session.add(rec)
        await db_session.commit()
        await db_session.refresh(rec)

        ownership_service = OwnershipService(db_session)

        with pytest.raises(ResourceNotFoundError):
            await ownership_service.get_user_recommendation(user_a.id, rec.id)

    @pytest.mark.asyncio
    async def test_user_a_cannot_access_user_b_roadmaps(self, db_session):
        """Test User A cannot access User B's roadmaps."""
        from app.models.business import BusinessProfile
        from app.models.roadmap import Roadmap
        from app.services.ownership import OwnershipService, ResourceNotFoundError
        auth_service = AuthService(db_session)

        user_a = await auth_service.register(
            email="usera4@example.com",
            full_name="User A4",
            password="StrongPassword123!",
        )
        user_b = await auth_service.register(
            email="userb4@example.com",
            full_name="User B4",
            password="StrongPassword123!",
        )

        # Create business profile for user_b
        profile_b = BusinessProfile(
            user_id=user_b.id,
            business_name="User B Business",
            business_type="Manufacturing",
            industry="Textiles",
            state="Maharashtra",
            district="Mumbai",
            business_structure="Private Limited",
            business_stage="Growth",
        )
        db_session.add(profile_b)
        await db_session.commit()
        await db_session.refresh(profile_b)

        roadmap = Roadmap(
            user_id=user_b.id,
            business_profile_id=profile_b.id,
            title="User B Roadmap",
            description="Test",
        )
        db_session.add(roadmap)
        await db_session.commit()
        await db_session.refresh(roadmap)

        ownership_service = OwnershipService(db_session)

        with pytest.raises(ResourceNotFoundError):
            await ownership_service.get_user_roadmap(user_a.id, roadmap.id)

    @pytest.mark.asyncio
    async def test_user_a_cannot_update_user_b_tasks(self, db_session):
        """Test User A cannot update User B's roadmap tasks."""
        from app.models.business import BusinessProfile
        from app.models.roadmap import Roadmap
        from app.models.task import RoadmapTask
        from app.services.ownership import OwnershipService, ResourceNotFoundError
        auth_service = AuthService(db_session)

        user_a = await auth_service.register(
            email="usera5@example.com",
            full_name="User A5",
            password="StrongPassword123!",
        )
        user_b = await auth_service.register(
            email="userb5@example.com",
            full_name="User B5",
            password="StrongPassword123!",
        )

        # Create business profile for user_b
        profile_b = BusinessProfile(
            user_id=user_b.id,
            business_name="User B Business",
            business_type="Manufacturing",
            industry="Textiles",
            state="Maharashtra",
            district="Mumbai",
            business_structure="Private Limited",
            business_stage="Growth",
        )
        db_session.add(profile_b)
        await db_session.commit()
        await db_session.refresh(profile_b)

        roadmap = Roadmap(
            user_id=user_b.id,
            business_profile_id=profile_b.id,
            title="User B Roadmap",
            description="Test",
        )
        db_session.add(roadmap)
        await db_session.commit()
        await db_session.refresh(roadmap)

        task = RoadmapTask(
            roadmap_id=roadmap.id,
            title="Task 1",
            description="Test task",
            sequence_number=1,
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        ownership_service = OwnershipService(db_session)

        with pytest.raises(ResourceNotFoundError):
            await ownership_service.get_user_roadmap_task(user_a.id, task.id)

    @pytest.mark.asyncio
    async def test_archived_business_profile_cannot_be_used_for_new_workflows(self, db_session):
        """Test that archived business profiles cannot be used for new workflows."""
        from app.services.ownership import OwnershipService, ResourceNotFoundError

        auth_service = AuthService(db_session)

        user = await auth_service.register(
            email="archived@example.com",
            full_name="Archived User",
            password="StrongPassword123!",
        )

        from app.models.business import BusinessProfile
        profile = BusinessProfile(
            user_id=user.id,
            business_name="Archived Business",
            business_type="Manufacturing",
            industry="Textiles",
            state="Maharashtra",
            district="Mumbai",
            business_structure="Private Limited",
            business_stage="Growth",
            is_deleted=True,  # Archived
        )
        db_session.add(profile)
        await db_session.commit()
        await db_session.refresh(profile)

        ownership_service = OwnershipService(db_session)

        # Normal get should fail for archived profiles
        with pytest.raises(ResourceNotFoundError):
            await ownership_service.get_user_business_profile(user.id, profile.id)

        # But archived get should work
        archived_profile = await ownership_service.get_user_business_profile_or_archived(user.id, profile.id)
        assert archived_profile.id == profile.id
        assert archived_profile.is_deleted is True


# Test API Endpoints
class TestAuthAPIEndpoints:
    """Tests for authentication API endpoints."""

    @pytest.mark.asyncio
    async def test_register_endpoint(self, client):
        """Test POST /api/v1/auth/register endpoint."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "api@example.com",
                "full_name": "API User",
                "password": "StrongPassword123!",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 1800
        assert data["user"]["email"] == "api@example.com"

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client):
        """Test register with duplicate email."""
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "dupapi@example.com",
                "full_name": "First User",
                "password": "StrongPassword123!",
            },
        )
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "dupapi@example.com",
                "full_name": "Second User",
                "password": "AnotherPassword123!",
            },
        )
        assert response.status_code == 409
        assert "already registered" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client):
        """Test register with invalid email."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalid-email",
                "full_name": "Invalid Email User",
                "password": "StrongPassword123!",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_weak_password(self, client):
        """Test register with weak password."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "weak@example.com",
                "full_name": "Weak Password User",
                "password": "weak",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_endpoint(self, client, db_session):
        """Test POST /api/v1/auth/login endpoint."""
        # First register
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "loginapi@example.com",
                "full_name": "Login API User",
                "password": "StrongPassword123!",
            },
        )

        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "loginapi@example.com",
                "password": "StrongPassword123!",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    @pytest.mark.asyncio
    async def test_login_incorrect_password(self, client):
        """Test login with incorrect password."""
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "wronglogin@example.com",
                "full_name": "Wrong Login User",
                "password": "StrongPassword123!",
            },
        )
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "wronglogin@example.com",
                "password": "WrongPassword123!",
            },
        )
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistentlogin@example.com",
                "password": "StrongPassword123!",
            },
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_endpoint(self, client):
        """Test POST /api/v1/auth/refresh endpoint."""
        # Register and login
        reg_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "refreshapi@example.com",
                "full_name": "Refresh API User",
                "password": "StrongPassword123!",
            },
        )
        refresh_token = reg_response.json()["refresh_token"]

        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["refresh_token"] != refresh_token  # Rotated

    @pytest.mark.asyncio
    async def test_refresh_old_token_invalid(self, client):
        """Test that old refresh token is invalid after rotation."""
        reg_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "refreshold@example.com",
                "full_name": "Refresh Old User",
                "password": "StrongPassword123!",
            },
        )
        refresh_token = reg_response.json()["refresh_token"]

        # First refresh
        await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        # Try to use old token
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_logout_endpoint(self, client):
        """Test POST /api/v1/auth/logout endpoint."""
        reg_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "logoutapi@example.com",
                "full_name": "Logout API User",
                "password": "StrongPassword123!",
            },
        )
        refresh_token = reg_response.json()["refresh_token"]

        response = await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        assert "Successfully logged out" in response.json()["message"]

        # Try to use revoked token
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me_endpoint(self, client):
        """Test GET /api/v1/auth/me endpoint."""
        reg_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "meapi@example.com",
                "full_name": "Me API User",
                "password": "StrongPassword123!",
            },
        )
        access_token = reg_response.json()["access_token"]

        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "meapi@example.com"
        assert data["full_name"] == "Me API User"
        assert "hashed_password" not in data

    @pytest.mark.asyncio
    async def test_me_endpoint_unauthorized(self, client):
        """Test GET /api/v1/auth/me without token."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me_endpoint_invalid_token(self, client):
        """Test GET /api/v1/auth/me with invalid token."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401


# Test Protected Route Access
class TestProtectedRouteAccess:
    """Tests for protected route access."""

    @pytest.mark.asyncio
    async def test_cross_user_access_denied(self, client, db_session):
        """Test that User A cannot access User B's resources via API."""
        from app.models.business import BusinessProfile

        # Create User A
        reg_a = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "crossa@example.com",
                "full_name": "Cross User A",
                "password": "StrongPassword123!",
            },
        )
        reg_a.json()["access_token"]

        # Create User B
        reg_b = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "crossb@example.com",
                "full_name": "Cross User B",
                "password": "StrongPassword123!",
            },
        )
        assert reg_b.status_code == 201

        # Get User B from database
        from sqlalchemy import select

        from app.models.user import User
        result = await db_session.execute(
            select(User).where(User.email == "crossb@example.com")
        )
        user_b = result.scalar_one()
        profile = BusinessProfile(
            user_id=user_b.id,
            business_name="User B Business",
            business_type="Manufacturing",
            industry="Textiles",
            state="Maharashtra",
            district="Mumbai",
            business_structure="Private Limited",
            business_stage="Growth",
        )
        db_session.add(profile)
        await db_session.commit()
        await db_session.refresh(profile)

        # User A tries to access User B's business profile
        # This would be through a business profile endpoint
        # For now, we test the ownership service directly
        from app.services.ownership import OwnershipService, ResourceNotFoundError
        ownership_service = OwnershipService(db_session)

        # Get User A's ID
        from sqlalchemy import select

        from app.models.user import User
        result = await db_session.execute(
            select(User).where(User.email == "crossa@example.com")
        )
        user_a = result.scalar_one()

        with pytest.raises(ResourceNotFoundError):
            await ownership_service.get_user_business_profile(user_a.id, profile.id)
