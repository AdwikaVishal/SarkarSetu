"""Business profile API tests."""
from datetime import UTC, datetime

import pytest

from app.schemas.business import BusinessProfileCreate


# Test Registration & Creation
class TestBusinessProfileCreation:
    """Tests for business profile creation."""

    @pytest.mark.asyncio
    async def test_create_business_profile(self, client, db_session):
        """Test creating a business profile via API."""
        # First register a user
        reg_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "bizuser@example.com",
                "full_name": "Biz User",
                "password": "StrongPassword123!",
            },
        )
        assert reg_response.status_code == 201
        token = reg_response.json()["access_token"]

        # Create business profile
        response = await client.post(
            "/api/v1/businesses/",
            json={
                "business_name": "Test Business",
                "business_type": "Manufacturing",
                "industry": "Textiles",
                "state": "Maharashtra",
                "district": "Mumbai",
                "annual_turnover": 5000000.00,
                "employee_count": 10,
                "sales_channels": ["online", "retail"],
                "business_structure": "Private Limited",
                "business_stage": "Growth",
                "description": "A test textile business",
                "city": "Mumbai",
                "pincode": "400001",
                "woman_owned": True,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["business_name"] == "Test Business"
        assert data["business_type"] == "Manufacturing"
        assert data["annual_turnover"] == 5000000.00
        assert data["employee_count"] == 10
        assert data["woman_owned"] is True
        assert data["is_deleted"] is False
        assert data["is_default"] is False
        assert data["id"] is not None

    @pytest.mark.asyncio
    async def test_create_business_profile_unauthenticated(self, client):
        """Test creating a business profile without authentication."""
        response = await client.post(
            "/api/v1/businesses/",
            json={
                "business_name": "Test Business",
                "business_type": "Manufacturing",
                "industry": "Textiles",
                "state": "Maharashtra",
                "district": "Mumbai",
                "business_structure": "Private Limited",
                "business_stage": "Growth",
            },
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_invalid_business_profile(self, client, db_session):
        """Test creating a business profile with invalid input."""
        # Register user
        reg_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalid@example.com",
                "full_name": "Invalid User",
                "password": "StrongPassword123!",
            },
        )
        token = reg_response.json()["access_token"]

        # Invalid pincode
        response = await client.post(
            "/api/v1/businesses/",
            json={
                "business_name": "Test Business",
                "business_type": "Manufacturing",
                "industry": "Textiles",
                "state": "Maharashtra",
                "district": "Mumbai",
                "business_structure": "Private Limited",
                "business_stage": "Growth",
                "pincode": "12345",  # Invalid - not 6 digits
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_negative_turnover(self, client, db_session):
        """Test creating business profile with negative turnover."""
        reg_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "neg@example.com",
                "full_name": "Neg User",
                "password": "StrongPassword123!",
            },
        )
        token = reg_response.json()["access_token"]

        response = await client.post(
            "/api/v1/businesses/",
            json={
                "business_name": "Test Business",
                "business_type": "Manufacturing",
                "industry": "Textiles",
                "state": "Maharashtra",
                "district": "Mumbai",
                "business_structure": "Private Limited",
                "business_stage": "Growth",
                "annual_turnover": -1000.00,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422


# Test Retrieval & Listing
class TestBusinessProfileRetrieval:
    """Tests for business profile retrieval."""

    @pytest.mark.asyncio
    async def test_create_and_retrieve_profile(self, client, db_session):
        """Test creating and then retrieving a business profile."""
        # Register user
        reg_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "retrieve@example.com",
                "full_name": "Retrieve User",
                "password": "StrongPassword123!",
            },
        )
        token = reg_response.json()["access_token"]

        # Create profile
        create_response = await client.post(
            "/api/v1/businesses/",
            json={
                "business_name": "Retrieve Test Business",
                "business_type": "Services",
                "industry": "IT Consulting",
                "state": "Karnataka",
                "district": "Bangalore",
                "business_structure": "LLP",
                "business_stage": "Startup",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert create_response.status_code == 201
        profile_id = create_response.json()["id"]

        # Retrieve profile
        get_response = await client.get(
            f"/api/v1/businesses/{profile_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["id"] == profile_id
        assert data["business_name"] == "Retrieve Test Business"

    @pytest.mark.asyncio
    async def test_cannot_access_another_users_profile(self, client, db_session):
        """Test that User A cannot access User B's business profile."""
        # Register User A
        reg_a = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "biz_a@example.com",
                "full_name": "User A",
                "password": "StrongPassword123!",
            },
        )
        token_a = reg_a.json()["access_token"]

        # Register User B
        reg_b = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "biz_b@example.com",
                "full_name": "User B",
                "password": "StrongPassword123!",
            },
        )
        token_b = reg_b.json()["access_token"]

        # User B creates profile
        create_b = await client.post(
            "/api/v1/businesses/",
            json={
                "business_name": "User B Business",
                "business_type": "Manufacturing",
                "industry": "Textiles",
                "state": "Maharashtra",
                "district": "Mumbai",
                "business_structure": "Private Limited",
                "business_stage": "Growth",
            },
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert create_b.status_code == 201
        profile_b_id = create_b.json()["id"]

        # User A tries to access User B's profile
        get_a = await client.get(
            f"/api/v1/businesses/{profile_b_id}",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert get_a.status_code == 404

    @pytest.mark.asyncio
    async def test_list_active_profiles_only(self, client, db_session):
        """Test that listing returns only active (non-archived) profiles."""
        # Register user
        reg_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "list@example.com",
                "full_name": "List User",
                "password": "StrongPassword123!",
            },
        )
        token = reg_response.json()["access_token"]

        # Create two profiles
        await client.post(
            "/api/v1/businesses/",
            json={
                "business_name": "Active Business",
                "business_type": "Manufacturing",
                "industry": "Textiles",
                "state": "Maharashtra",
                "district": "Mumbai",
                "business_structure": "Private Limited",
                "business_stage": "Growth",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        # Create and archive second profile
        create_response = await client.post(
            "/api/v1/businesses/",
            json={
                "business_name": "Archived Business",
                "business_type": "Services",
                "industry": "IT",
                "state": "Karnataka",
                "district": "Bangalore",
                "business_structure": "LLP",
                "business_stage": "Startup",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        archived_id = create_response.json()["id"]

        await client.delete(
            f"/api/v1/businesses/{archived_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        # List active profiles - should only have 1
        list_response = await client.get(
            "/api/v1/businesses/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert list_response.status_code == 200
        data = list_response.json()
        assert data["total"] == 1
        assert data["items"][0]["business_name"] == "Active Business"


# Test Update
class TestBusinessProfileUpdate:
    """Tests for business profile updates."""

    @pytest.mark.asyncio
    async def test_update_business_profile(self, client, db_session):
        """Test updating a business profile."""
        reg_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "update@example.com",
                "full_name": "Update User",
                "password": "StrongPassword123!",
            },
        )
        token = reg_response.json()["access_token"]

        create_response = await client.post(
            "/api/v1/businesses/",
            json={
                "business_name": "Original Name",
                "business_type": "Manufacturing",
                "industry": "Textiles",
                "state": "Maharashtra",
                "district": "Mumbai",
                "business_structure": "Private Limited",
                "business_stage": "Growth",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        profile_id = create_response.json()["id"]

        # Partial update
        update_response = await client.patch(
            f"/api/v1/businesses/{profile_id}",
            json={
                "business_name": "Updated Name",
                "annual_turnover": 10000000.00,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["business_name"] == "Updated Name"
        assert data["annual_turnover"] == 10000000.00

        # Verify unchanged fields preserved
        get_response = await client.get(
            f"/api/v1/businesses/{profile_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_response.json()["business_type"] == "Manufacturing"
        assert get_response.json()["industry"] == "Textiles"

    @pytest.mark.asyncio
    async def test_cannot_update_another_users_profile(self, client, db_session):
        """Test that User A cannot update User B's profile."""
        # Register and create profile for User B
        reg_b = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "update_b@example.com",
                "full_name": "User B",
                "password": "StrongPassword123!",
            },
        )
        token_b = reg_b.json()["access_token"]

        create_b = await client.post(
            "/api/v1/businesses/",
            json={
                "business_name": "User B Business",
                "business_type": "Manufacturing",
                "industry": "Textiles",
                "state": "Maharashtra",
                "district": "Mumbai",
                "business_structure": "Private Limited",
                "business_stage": "Growth",
            },
            headers={"Authorization": f"Bearer {token_b}"},
        )
        profile_b_id = create_b.json()["id"]

        # Register User A
        reg_a = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "update_a@example.com",
                "full_name": "User A",
                "password": "StrongPassword123!",
            },
        )
        token_a = reg_a.json()["access_token"]

        # User A tries to update User B's profile
        update_a = await client.patch(
            f"/api/v1/businesses/{profile_b_id}",
            json={"business_name": "Hacked Name"},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert update_a.status_code == 404


# Test Archival & Restoration
class TestBusinessProfileArchive:
    """Tests for business profile archival and restoration."""

    @pytest.mark.asyncio
    async def test_archive_business_profile(self, client, db_session):
        """Test archiving a business profile."""
        reg_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "archive@example.com",
                "full_name": "Archive User",
                "password": "StrongPassword123!",
            },
        )
        token = reg_response.json()["access_token"]

        create_response = await client.post(
            "/api/v1/businesses/",
            json={
                "business_name": "To Archive",
                "business_type": "Manufacturing",
                "industry": "Textiles",
                "state": "Maharashtra",
                "district": "Mumbai",
                "business_structure": "Private Limited",
                "business_stage": "Growth",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        profile_id = create_response.json()["id"]

        # Archive
        archive_response = await client.delete(
            f"/api/v1/businesses/{profile_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert archive_response.status_code == 204

        # Verify archived profile not in active listing
        list_response = await client.get(
            "/api/v1/businesses/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert list_response.json()["total"] == 0

        # Verify archived profile in archived listing
        archived_response = await client.get(
            "/api/v1/businesses/archived",
            headers={"Authorization": f"Bearer {token}"},
        )
        archived_data = archived_response.json()
        assert archived_data["total"] == 1
        assert archived_data["items"][0]["is_deleted"] is True

    @pytest.mark.asyncio
    async def test_restore_archived_profile(self, client, db_session):
        """Test restoring an archived business profile."""
        reg_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "restore@example.com",
                "full_name": "Restore User",
                "password": "StrongPassword123!",
            },
        )
        token = reg_response.json()["access_token"]

        create_response = await client.post(
            "/api/v1/businesses/",
            json={
                "business_name": "To Restore",
                "business_type": "Manufacturing",
                "industry": "Textiles",
                "state": "Maharashtra",
                "district": "Mumbai",
                "business_structure": "Private Limited",
                "business_stage": "Growth",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        profile_id = create_response.json()["id"]

        # Archive then restore
        await client.delete(
            f"/api/v1/businesses/{profile_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        restore_response = await client.post(
            f"/api/v1/businesses/{profile_id}/restore",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert restore_response.status_code == 200
        assert restore_response.json()["is_deleted"] is False
        assert restore_response.json()["deleted_at"] is None

        # Verify profile is back in active listing
        list_response = await client.get(
            "/api/v1/businesses/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert list_response.json()["total"] == 1

    @pytest.mark.asyncio
    async def test_archived_profile_cannot_be_used_for_new_workflows(self, client, db_session):
        """Test that archived profiles cannot be used in new workflows."""
        # This test verifies that archived profiles are excluded
        # from active listing and default selection
        reg_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "workflow@example.com",
                "full_name": "Workflow User",
                "password": "StrongPassword123!",
            },
        )
        token = reg_response.json()["access_token"]

        create_response = await client.post(
            "/api/v1/businesses/",
            json={
                "business_name": "Workflow Business",
                "business_type": "Manufacturing",
                "industry": "Textiles",
                "state": "Maharashtra",
                "district": "Mumbai",
                "business_structure": "Private Limited",
                "business_stage": "Growth",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        profile_id = create_response.json()["id"]

        # Archive the profile
        await client.delete(
            f"/api/v1/businesses/{profile_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Try to set archived profile as default - should fail
        default_response = await client.patch(
            f"/api/v1/businesses/{profile_id}/default",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert default_response.status_code == 404


# Test Default Business Profile
class TestDefaultBusinessProfile:
    """Tests for default business profile selection."""

    @pytest.mark.asyncio
    async def test_set_default_business_profile(self, client, db_session):
        """Test setting a business profile as default."""
        reg_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "default@example.com",
                "full_name": "Default User",
                "password": "StrongPassword123!",
            },
        )
        token = reg_response.json()["access_token"]

        # Create two profiles
        create_a = await client.post(
            "/api/v1/businesses/",
            json={
                "business_name": "Business A",
                "business_type": "Manufacturing",
                "industry": "Textiles",
                "state": "Maharashtra",
                "district": "Mumbai",
                "business_structure": "Private Limited",
                "business_stage": "Growth",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        profile_a_id = create_a.json()["id"]

        create_b = await client.post(
            "/api/v1/businesses/",
            json={
                "business_name": "Business B",
                "business_type": "Services",
                "industry": "IT",
                "state": "Karnataka",
                "district": "Bangalore",
                "business_structure": "LLP",
                "business_stage": "Startup",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        profile_b_id = create_b.json()["id"]

        # Set Business A as default
        default_a = await client.patch(
            f"/api/v1/businesses/{profile_a_id}/default",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert default_a.status_code == 200
        assert default_a.json()["is_default"] is True

        # Set Business B as default - should unset A
        default_b = await client.patch(
            f"/api/v1/businesses/{profile_b_id}/default",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert default_b.status_code == 200
        assert default_b.json()["is_default"] is True

        # Verify A is no longer default
        get_a = await client.get(
            f"/api/v1/businesses/{profile_a_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_a.json()["is_default"] is False

    @pytest.mark.asyncio
    async def test_cannot_set_archived_profile_as_default(self, client, db_session):
        """Test that archived profiles cannot be set as default."""
        reg_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "default_arch@example.com",
                "full_name": "Default Arch User",
                "password": "StrongPassword123!",
            },
        )
        token = reg_response.json()["access_token"]

        create_response = await client.post(
            "/api/v1/businesses/",
            json={
                "business_name": "To Archive",
                "business_type": "Manufacturing",
                "industry": "Textiles",
                "state": "Maharashtra",
                "district": "Mumbai",
                "business_structure": "Private Limited",
                "business_stage": "Growth",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        profile_id = create_response.json()["id"]

        # Archive
        await client.delete(
            f"/api/v1/businesses/{profile_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Try to set as default - should fail
        default_response = await client.patch(
            f"/api/v1/businesses/{profile_id}/default",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert default_response.status_code == 404

    @pytest.mark.asyncio
    async def test_cannot_set_another_users_profile_as_default(self, client, db_session):
        """Test that User A cannot set User B's profile as default."""
        # User B creates profile
        reg_b = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "default_b@example.com",
                "full_name": "User B",
                "password": "StrongPassword123!",
            },
        )
        token_b = reg_b.json()["access_token"]

        create_b = await client.post(
            "/api/v1/businesses/",
            json={
                "business_name": "User B Business",
                "business_type": "Manufacturing",
                "industry": "Textiles",
                "state": "Maharashtra",
                "district": "Mumbai",
                "business_structure": "Private Limited",
                "business_stage": "Growth",
            },
            headers={"Authorization": f"Bearer {token_b}"},
        )
        profile_b_id = create_b.json()["id"]

        # Register User A
        reg_a = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "default_a@example.com",
                "full_name": "User A",
                "password": "StrongPassword123!",
            },
        )
        token_a = reg_a.json()["access_token"]

        # User A tries to set User B's profile as default
        default_a = await client.patch(
            f"/api/v1/businesses/{profile_b_id}/default",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert default_a.status_code == 404


# Test Service Layer
class TestBusinessService:
    """Tests for business service layer."""

    @pytest.mark.asyncio
    async def test_service_create_profile(self, db_session):
        """Test service layer profile creation."""
        from app.services.auth_service import AuthService

        auth_service = AuthService(db_session)
        user = await auth_service.register(
            email="service@example.com",
            full_name="Service User",
            password="StrongPassword123!",
        )

        from app.services.business_service import BusinessService
        service = BusinessService(db_session)

        profile_data = BusinessProfileCreate(
            business_name="Service Business",
            business_type="Manufacturing",
            industry="Textiles",
            state="Maharashtra",
            district="Mumbai",
            business_structure="Private Limited",
            business_stage="Growth",
        )

        profile = await service.create_business_profile(user.id, profile_data)
        assert profile.id is not None
        assert profile.business_name == "Service Business"
        assert profile.user_id == user.id

    @pytest.mark.asyncio
    async def test_service_get_profile(self, db_session):
        """Test service layer profile retrieval."""
        from app.services.auth_service import AuthService

        auth_service = AuthService(db_session)
        user = await auth_service.register(
            email="service_get@example.com",
            full_name="Service Get User",
            password="StrongPassword123!",
        )

        from app.services.business_service import BusinessService
        service = BusinessService(db_session)

        profile_data = BusinessProfileCreate(
            business_name="Service Get Business",
            business_type="Manufacturing",
            industry="Textiles",
            state="Maharashtra",
            district="Mumbai",
            business_structure="Private Limited",
            business_stage="Growth",
        )

        profile = await service.create_business_profile(user.id, profile_data)
        retrieved = await service.get_business_profile(user.id, profile.id)
        assert retrieved.id == profile.id
        assert retrieved.business_name == "Service Get Business"


# Test Migration & Schema Validation
class TestBusinessProfileSchema:
    """Tests for business profile schema validation."""

    def test_business_profile_create_validation(self):
        """Test that BusinessProfileCreate validates correctly."""

        profile = BusinessProfileCreate(
            business_name="Valid Business",
            business_type="Manufacturing",
            industry="Textiles",
            state="Maharashtra",
            district="Mumbai",
            business_structure="Private Limited",
            business_stage="Growth",
        )
        assert profile.business_name == "Valid Business"

    def test_pincode_validation(self):
        """Test PIN code validation."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            BusinessProfileCreate(
                business_name="Test",
                business_type="Manufacturing",
                industry="Textiles",
                state="MH",
                district="Mumbai",
                business_structure="Pvt Ltd",
                business_stage="Growth",
                pincode="12345",  # Invalid - not 6 digits
            )

        # Valid pincode
        profile = BusinessProfileCreate(
            business_name="Test",
            business_type="Manufacturing",
            industry="Textiles",
            state="MH",
            district="Mumbai",
            business_structure="Pvt Ltd",
            business_stage="Growth",
            pincode="400001",
        )
        assert profile.pincode == "400001"

    def test_gstin_validation(self):
        """Test GSTIN validation."""
        from pydantic import ValidationError

        # Invalid GSTIN - starts with letters instead of digits
        with pytest.raises(ValidationError):
            BusinessProfileCreate(
                business_name="Test",
                business_type="Manufacturing",
                industry="Textiles",
                state="MH",
                district="Mumbai",
                business_structure="Pvt Ltd",
                business_stage="Growth",
                gstin="ABCDEFGHIJKLMNO",  # Invalid - starts with letters
            )

        # Valid GSTIN format (15 chars, starts with 2-digit state code)
        profile = BusinessProfileCreate(
            business_name="Test",
            business_type="Manufacturing",
            industry="Textiles",
            state="MH",
            district="Mumbai",
            business_structure="Pvt Ltd",
            business_stage="Growth",
            gstin="27AAAAA0000A1Z5",
        )
        assert profile.gstin == "27AAAAA0000A1Z5"

    def test_date_of_establishment_validation(self):
        """Test date of establishment validation."""
        from datetime import timedelta

        from pydantic import ValidationError

        # Future date
        future_date = datetime.now(UTC) + timedelta(days=30)
        with pytest.raises(ValidationError):
            BusinessProfileCreate(
                business_name="Test",
                business_type="Manufacturing",
                industry="Textiles",
                state="MH",
                district="Mumbai",
                business_structure="Pvt Ltd",
                business_stage="Growth",
                date_of_establishment=future_date,
            )

        # Valid past date
        past_date = datetime(2020, 1, 1, tzinfo=UTC)
        profile = BusinessProfileCreate(
            business_name="Test",
            business_type="Manufacturing",
            industry="Textiles",
            state="MH",
            district="Mumbai",
            business_structure="Pvt Ltd",
            business_stage="Growth",
            date_of_establishment=past_date,
        )
        assert profile.date_of_establishment == past_date


class TestBusinessProfileEdgeCases:
    """Edge case tests."""

    @pytest.mark.asyncio
    async def test_create_profile_without_optional_fields(self, client):
        """Test creating profile with only required fields."""
        reg_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "minimal@example.com",
                "full_name": "Minimal User",
                "password": "StrongPassword123!",
            },
        )
        token = reg_response.json()["access_token"]

        response = await client.post(
            "/api/v1/businesses/",
            json={
                "business_name": "Minimal Business",
                "business_type": "Manufacturing",
                "industry": "Textiles",
                "state": "Maharashtra",
                "district": "Mumbai",
                "business_structure": "Private Limited",
                "business_stage": "Growth",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["annual_turnover"] is None
        assert data["employee_count"] is None
        assert data["sales_channels"] == []

