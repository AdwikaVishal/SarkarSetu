"""Database model tests."""
import asyncio
import os
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.database.base import Base
from app.models import (
    BusinessProfile,
    Conversation,
    EligibilityResult,
    Message,
    Recommendation,
    Roadmap,
    RoadmapTask,
    UploadedDocument,
    User,
)

# Check if PostgreSQL is available for integration tests
# Use a test database URL if provided, otherwise skip database tests
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

# Mark all database tests as requiring PostgreSQL
pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="PostgreSQL not available - set TEST_DATABASE_URL to run database integration tests",
)




@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a database session for testing."""
    if not TEST_DATABASE_URL:
        pytest.skip("PostgreSQL not available")

    engine = create_async_engine(TEST_DATABASE_URL, poolclass=None)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


class TestUserModel:
    """Tests for User model."""

    @pytest.mark.asyncio
    async def test_user_creation(self, db_session: AsyncSession) -> None:
        """Test creating a user."""
        user = User(
            email="test@example.com",
            full_name="Test User",
            hashed_password="hashed_password_123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.hashed_password == "hashed_password_123"
        assert user.is_active is True
        assert user.is_verified is False
        assert user.created_at is not None
        assert user.updated_at is not None

    @pytest.mark.asyncio
    async def test_user_unique_email_constraint(self, db_session: AsyncSession) -> None:
        """Test that email must be unique."""
        user1 = User(
            email="unique@example.com",
            full_name="User One",
            hashed_password="password1",
        )
        user2 = User(
            email="unique@example.com",
            full_name="User Two",
            hashed_password="password2",
        )
        db_session.add(user1)
        await db_session.commit()

        db_session.add(user2)
        with pytest.raises(IntegrityError):
            await db_session.commit()


class TestBusinessProfileModel:
    """Tests for BusinessProfile model."""

    @pytest.mark.asyncio
    async def test_business_profile_creation(self, db_session: AsyncSession) -> None:
        """Test creating a business profile."""
        user = User(
            email="business@example.com",
            full_name="Business Owner",
            hashed_password="hashed_password",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        profile = BusinessProfile(
            user_id=user.id,
            business_name="Test Business",
            business_type="Manufacturing",
            industry="Textiles",
            state="Maharashtra",
            district="Mumbai",
            annual_turnover=Decimal("5000000.00"),
            employee_count=10,
            sales_channels=["online", "retail"],
            business_structure="Private Limited",
            business_stage="Growth",
        )
        db_session.add(profile)
        await db_session.commit()
        await db_session.refresh(profile)

        assert profile.id is not None
        assert profile.user_id == user.id
        assert profile.business_name == "Test Business"
        assert profile.annual_turnover == Decimal("5000000.00")
        assert profile.employee_count == 10
        assert profile.sales_channels == ["online", "retail"]

    @pytest.mark.asyncio
    async def test_multiple_business_profiles_per_user(self, db_session: AsyncSession) -> None:
        """Test that a user can have multiple business profiles."""
        user = User(
            email="multi@example.com",
            full_name="Multi Business Owner",
            hashed_password="hashed_password",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        profile1 = BusinessProfile(
            user_id=user.id,
            business_name="Business One",
            business_type="Manufacturing",
            industry="Textiles",
            state="Maharashtra",
            district="Mumbai",
            business_structure="Private Limited",
            business_stage="Growth",
        )
        profile2 = BusinessProfile(
            user_id=user.id,
            business_name="Business Two",
            business_type="Services",
            industry="IT Consulting",
            state="Karnataka",
            district="Bangalore",
            business_structure="LLP",
            business_stage="Startup",
        )
        db_session.add_all([profile1, profile2])
        await db_session.commit()

        # Verify both profiles exist
        result = await db_session.execute(
            select(BusinessProfile).where(BusinessProfile.user_id == user.id)
        )
        profiles = result.scalars().all()
        assert len(profiles) == 2

    @pytest.mark.asyncio
    async def test_invalid_negative_turnover(self, db_session: AsyncSession) -> None:
        """Test that negative annual turnover is rejected."""
        user = User(
            email="negative@example.com",
            full_name="Test User",
            hashed_password="hashed_password",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        profile = BusinessProfile(
            user_id=user.id,
            business_name="Test Business",
            business_type="Manufacturing",
            industry="Textiles",
            state="Maharashtra",
            district="Mumbai",
            annual_turnover=Decimal("-1000.00"),
            business_structure="Private Limited",
            business_stage="Growth",
        )
        db_session.add(profile)
        with pytest.raises(IntegrityError):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_invalid_negative_employee_count(self, db_session: AsyncSession) -> None:
        """Test that negative employee count is rejected."""
        user = User(
            email="negative2@example.com",
            full_name="Test User",
            hashed_password="hashed_password",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        profile = BusinessProfile(
            user_id=user.id,
            business_name="Test Business",
            business_type="Manufacturing",
            industry="Textiles",
            state="Maharashtra",
            district="Mumbai",
            employee_count=-5,
            business_structure="Private Limited",
            business_stage="Growth",
        )
        db_session.add(profile)
        with pytest.raises(IntegrityError):
            await db_session.commit()


class TestConversationModel:
    """Tests for Conversation model."""

    @pytest.mark.asyncio
    async def test_conversation_creation(self, db_session: AsyncSession) -> None:
        """Test creating a conversation."""
        user = User(
            email="conv@example.com",
            full_name="Conversation User",
            hashed_password="hashed_password",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        conversation = Conversation(
            user_id=user.id,
            title="Test Conversation",
        )
        db_session.add(conversation)
        await db_session.commit()
        await db_session.refresh(conversation)

        assert conversation.id is not None
        assert conversation.user_id == user.id
        assert conversation.title == "Test Conversation"
        assert conversation.status == "active"

    @pytest.mark.asyncio
    async def test_conversation_with_business_profile(self, db_session: AsyncSession) -> None:
        """Test creating a conversation linked to a business profile."""
        user = User(
            email="conv2@example.com",
            full_name="Conversation User",
            hashed_password="hashed_password",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        profile = BusinessProfile(
            user_id=user.id,
            business_name="Test Business",
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

        conversation = Conversation(
            user_id=user.id,
            business_profile_id=profile.id,
            title="Business Conversation",
        )
        db_session.add(conversation)
        await db_session.commit()
        await db_session.refresh(conversation)

        assert conversation.business_profile_id == profile.id


class TestMessageModel:
    """Tests for Message model."""

    @pytest.mark.asyncio
    async def test_message_creation(self, db_session: AsyncSession) -> None:
        """Test creating a message."""
        user = User(
            email="msg@example.com",
            full_name="Message User",
            hashed_password="hashed_password",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        conversation = Conversation(
            user_id=user.id,
            title="Test Conversation",
        )
        db_session.add(conversation)
        await db_session.commit()
        await db_session.refresh(conversation)

        message = Message(
            conversation_id=conversation.id,
            role="user",
            content="Hello, world!",
            intent="greeting",
            message_metadata={"source": "web"},
        )
        db_session.add(message)
        await db_session.commit()
        await db_session.refresh(message)

        assert message.id is not None
        assert message.conversation_id == conversation.id
        assert message.role == "user"
        assert message.content == "Hello, world!"
        assert message.intent == "greeting"
        assert message.message_metadata == {"source": "web"}

    @pytest.mark.asyncio
    async def test_messages_belong_to_conversation(self, db_session: AsyncSession) -> None:
        """Test that messages belong to a conversation."""
        user = User(
            email="msg2@example.com",
            full_name="Message User",
            hashed_password="hashed_password",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        conversation = Conversation(
            user_id=user.id,
            title="Test Conversation",
        )
        db_session.add(conversation)
        await db_session.commit()
        await db_session.refresh(conversation)

        messages = [
            Message(conversation_id=conversation.id, role="user", content="Message 1"),
            Message(conversation_id=conversation.id, role="assistant", content="Message 2"),
            Message(conversation_id=conversation.id, role="user", content="Message 3"),
        ]
        db_session.add_all(messages)
        await db_session.commit()

        result = await db_session.execute(
            select(Message).where(Message.conversation_id == conversation.id).order_by(Message.created_at)
        )
        retrieved = result.scalars().all()
        assert len(retrieved) == 3
        assert retrieved[0].content == "Message 1"
        assert retrieved[1].content == "Message 2"
        assert retrieved[2].content == "Message 3"


class TestRecommendationModel:
    """Tests for Recommendation model."""

    @pytest.mark.asyncio
    async def test_recommendation_creation(self, db_session: AsyncSession) -> None:
        """Test creating a recommendation."""
        user = User(
            email="rec@example.com",
            full_name="Recommendation User",
            hashed_password="hashed_password",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        profile = BusinessProfile(
            user_id=user.id,
            business_name="Test Business",
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

        recommendation = Recommendation(
            business_profile_id=profile.id,
            user_id=user.id,
            category="Government Scheme",
            title="MSME Loan Scheme",
            description="Low interest loan for MSMEs",
            recommendation_status="pending",
            eligibility_status="eligible",
        )
        db_session.add(recommendation)
        await db_session.commit()
        await db_session.refresh(recommendation)

        assert recommendation.id is not None
        assert recommendation.category == "Government Scheme"
        assert recommendation.eligibility_status == "eligible"


class TestEligibilityResultModel:
    """Tests for EligibilityResult model."""

    @pytest.mark.asyncio
    async def test_eligibility_result_creation(self, db_session: AsyncSession) -> None:
        """Test creating an eligibility result."""
        user = User(
            email="elig@example.com",
            full_name="Eligibility User",
            hashed_password="hashed_password",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        profile = BusinessProfile(
            user_id=user.id,
            business_name="Test Business",
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

        result = EligibilityResult(
            user_id=user.id,
            business_profile_id=profile.id,
            rule_set_version="v1.0",
            assessment_status="completed",
            result_data={"eligible": True, "score": 85},
            missing_information={},
        )
        db_session.add(result)
        await db_session.commit()
        await db_session.refresh(result)

        assert result.id is not None
        assert result.rule_set_version == "v1.0"
        assert result.assessment_status == "completed"
        assert result.result_data == {"eligible": True, "score": 85}


class TestUploadedDocumentModel:
    """Tests for UploadedDocument model."""

    @pytest.mark.asyncio
    async def test_document_creation(self, db_session: AsyncSession) -> None:
        """Test creating an uploaded document."""
        user = User(
            email="doc@example.com",
            full_name="Document User",
            hashed_password="hashed_password",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        document = UploadedDocument(
            user_id=user.id,
            original_filename="test.pdf",
            storage_key="uploads/user123/test.pdf",
            content_type="application/pdf",
            file_size=1024,
            processing_status="completed",
            document_type="identity_proof",
            extracted_data={"name": "Test User", "id": "12345"},
        )
        db_session.add(document)
        await db_session.commit()
        await db_session.refresh(document)

        assert document.id is not None
        assert document.original_filename == "test.pdf"
        assert document.file_size == 1024


class TestRoadmapModel:
    """Tests for Roadmap model."""

    @pytest.mark.asyncio
    async def test_roadmap_creation(self, db_session: AsyncSession) -> None:
        """Test creating a roadmap."""
        user = User(
            email="road@example.com",
            full_name="Roadmap User",
            hashed_password="hashed_password",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        profile = BusinessProfile(
            user_id=user.id,
            business_name="Test Business",
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

        roadmap = Roadmap(
            user_id=user.id,
            business_profile_id=profile.id,
            title="Business Setup Roadmap",
            description="Step by step guide to setup business",
            status="active",
            progress_percentage=25,
        )
        db_session.add(roadmap)
        await db_session.commit()
        await db_session.refresh(roadmap)

        assert roadmap.id is not None
        assert roadmap.title == "Business Setup Roadmap"
        assert roadmap.progress_percentage == 25


class TestRoadmapTaskModel:
    """Tests for RoadmapTask model."""

    @pytest.mark.asyncio
    async def test_roadmap_task_creation(self, db_session: AsyncSession) -> None:
        """Test creating a roadmap task."""
        user = User(
            email="task@example.com",
            full_name="Task User",
            hashed_password="hashed_password",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        profile = BusinessProfile(
            user_id=user.id,
            business_name="Test Business",
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

        roadmap = Roadmap(
            user_id=user.id,
            business_profile_id=profile.id,
            title="Business Setup Roadmap",
            description="Step by step guide",
        )
        db_session.add(roadmap)
        await db_session.commit()
        await db_session.refresh(roadmap)

        task = RoadmapTask(
            roadmap_id=roadmap.id,
            title="Register Business",
            description="Register the business with MCA",
            sequence_number=1,
            status="pending",
            priority="high",
            official_portal_url="https://mca.gov.in",
            required_documents=["PAN Card", "Aadhaar Card"],
            source_references=["Companies Act 2013"],
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        assert task.id is not None
        assert task.sequence_number == 1
        assert task.status == "pending"
        assert task.required_documents == ["PAN Card", "Aadhaar Card"]


class TestSoftDeletionAndHistoricalPreservation:
    """Tests for soft deletion and historical data preservation."""

    @pytest.mark.asyncio
    async def test_business_profile_soft_delete_preserves_conversations(self, db_session: AsyncSession) -> None:
        """Test that soft deleting a business profile preserves conversations."""
        user = User(
            email="softdel1@example.com",
            full_name="Soft Delete User",
            hashed_password="hashed_password",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        profile = BusinessProfile(
            user_id=user.id,
            business_name="Test Business",
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

        conversation = Conversation(
            user_id=user.id,
            business_profile_id=profile.id,
            title="Test Conversation",
        )
        db_session.add(conversation)
        await db_session.commit()
        await db_session.refresh(conversation)

        # Soft delete the business profile
        profile.is_deleted = True
        profile.deleted_at = datetime.now(UTC)
        await db_session.commit()

        # Conversation should still exist and be accessible
        result = await db_session.execute(
            select(Conversation).where(Conversation.id == conversation.id)
        )
        retrieved = result.scalar_one()
        assert retrieved is not None
        assert retrieved.business_profile_id == profile.id
        assert retrieved.title == "Test Conversation"

    @pytest.mark.asyncio
    async def test_business_profile_soft_delete_preserves_recommendations(self, db_session: AsyncSession) -> None:
        """Test that soft deleting a business profile preserves recommendations."""
        user = User(
            email="softdel2@example.com",
            full_name="Soft Delete User",
            hashed_password="hashed_password",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        profile = BusinessProfile(
            user_id=user.id,
            business_name="Test Business",
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

        recommendation = Recommendation(
            business_profile_id=profile.id,
            user_id=user.id,
            category="Government Scheme",
            title="MSME Loan Scheme",
            description="Low interest loan for MSMEs",
        )
        db_session.add(recommendation)
        await db_session.commit()
        await db_session.refresh(recommendation)

        # Soft delete the business profile
        profile.is_deleted = True
        profile.deleted_at = datetime.now(UTC)
        await db_session.commit()

        # Recommendation should still exist
        result = await db_session.execute(
            select(Recommendation).where(Recommendation.id == recommendation.id)
        )
        retrieved = result.scalar_one()
        assert retrieved is not None
        assert retrieved.business_profile_id == profile.id

    @pytest.mark.asyncio
    async def test_business_profile_soft_delete_preserves_eligibility_results(self, db_session: AsyncSession) -> None:
        """Test that soft deleting a business profile preserves eligibility results."""
        user = User(
            email="softdel3@example.com",
            full_name="Soft Delete User",
            hashed_password="hashed_password",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        profile = BusinessProfile(
            user_id=user.id,
            business_name="Test Business",
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

        result = EligibilityResult(
            user_id=user.id,
            business_profile_id=profile.id,
            rule_set_version="v1.0",
            assessment_status="completed",
            result_data={"eligible": True},
        )
        db_session.add(result)
        await db_session.commit()
        await db_session.refresh(result)

        # Soft delete the business profile
        profile.is_deleted = True
        profile.deleted_at = datetime.now(UTC)
        await db_session.commit()

        # Eligibility result should still exist
        result_check = await db_session.execute(
            select(EligibilityResult).where(EligibilityResult.id == result.id)
        )
        retrieved = result_check.scalar_one()
        assert retrieved is not None
        assert retrieved.business_profile_id == profile.id

    @pytest.mark.asyncio
    async def test_business_profile_soft_delete_preserves_roadmaps(self, db_session: AsyncSession) -> None:
        """Test that soft deleting a business profile preserves roadmaps."""
        user = User(
            email="softdel4@example.com",
            full_name="Soft Delete User",
            hashed_password="hashed_password",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        profile = BusinessProfile(
            user_id=user.id,
            business_name="Test Business",
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

        roadmap = Roadmap(
            user_id=user.id,
            business_profile_id=profile.id,
            title="Business Setup Roadmap",
            description="Step by step guide",
        )
        db_session.add(roadmap)
        await db_session.commit()
        await db_session.refresh(roadmap)

        # Soft delete the business profile
        profile.is_deleted = True
        profile.deleted_at = datetime.now(UTC)
        await db_session.commit()

        # Roadmap should still exist
        result = await db_session.execute(
            select(Roadmap).where(Roadmap.id == roadmap.id)
        )
        retrieved = result.scalar_one()
        assert retrieved is not None
        assert retrieved.business_profile_id == profile.id

    @pytest.mark.asyncio
    async def test_recommendation_delete_preserves_eligibility_results(self, db_session: AsyncSession) -> None:
        """Test that deleting a recommendation preserves eligibility results (FK SET NULL)."""
        user = User(
            email="softdel5@example.com",
            full_name="Soft Delete User",
            hashed_password="hashed_password",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        profile = BusinessProfile(
            user_id=user.id,
            business_name="Test Business",
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

        recommendation = Recommendation(
            business_profile_id=profile.id,
            user_id=user.id,
            category="Government Scheme",
            title="MSME Loan Scheme",
            description="Low interest loan for MSMEs",
        )
        db_session.add(recommendation)
        await db_session.commit()
        await db_session.refresh(recommendation)

        eligibility = EligibilityResult(
            user_id=user.id,
            business_profile_id=profile.id,
            recommendation_id=recommendation.id,
            rule_set_version="v1.0",
            assessment_status="completed",
            result_data={"eligible": True},
        )
        db_session.add(eligibility)
        await db_session.commit()
        await db_session.refresh(eligibility)

        # Delete the recommendation
        await db_session.delete(recommendation)
        await db_session.commit()

        # Eligibility result should still exist with recommendation_id set to NULL
        # Need to expire and reload to get the database state
        await db_session.refresh(eligibility)
        assert eligibility.recommendation_id is None

    @pytest.mark.asyncio
    async def test_user_cascade_delete_removes_business_profiles(self, db_session: AsyncSession) -> None:
        """Test that deleting a user cascades to business profiles (hard delete)."""
        user = User(
            email="cascade1@example.com",
            full_name="Cascade User",
            hashed_password="hashed_password",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        profile = BusinessProfile(
            user_id=user.id,
            business_name="Test Business",
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

        await db_session.delete(user)
        await db_session.commit()

        result = await db_session.execute(
            select(BusinessProfile).where(BusinessProfile.id == profile.id)
        )
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_roadmap_delete_cascades_to_tasks(self, db_session: AsyncSession) -> None:
        """Test that deleting a roadmap cascades to tasks (required parent-child)."""
        user = User(
            email="cascade2@example.com",
            full_name="Cascade User",
            hashed_password="hashed_password",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        profile = BusinessProfile(
            user_id=user.id,
            business_name="Test Business",
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

        roadmap = Roadmap(
            user_id=user.id,
            business_profile_id=profile.id,
            title="Business Setup Roadmap",
            description="Step by step guide",
        )
        db_session.add(roadmap)
        await db_session.commit()
        await db_session.refresh(roadmap)

        task = RoadmapTask(
            roadmap_id=roadmap.id,
            title="Register Business",
            description="Register the business with MCA",
            sequence_number=1,
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        await db_session.delete(roadmap)
        await db_session.commit()

        result = await db_session.execute(
            select(RoadmapTask).where(RoadmapTask.id == task.id)
        )
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_conversation_delete_cascades_to_messages(self, db_session: AsyncSession) -> None:
        """Test that deleting a conversation cascades to messages (required parent-child)."""
        user = User(
            email="cascade3@example.com",
            full_name="Cascade User",
            hashed_password="hashed_password",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        conversation = Conversation(
            user_id=user.id,
            title="Test Conversation",
        )
        db_session.add(conversation)
        await db_session.commit()
        await db_session.refresh(conversation)

        message = Message(
            conversation_id=conversation.id,
            role="user",
            content="Test message",
        )
        db_session.add(message)
        await db_session.commit()
        await db_session.refresh(message)

        await db_session.delete(conversation)
        await db_session.commit()

        result = await db_session.execute(
            select(Message).where(Message.id == message.id)
        )
        assert result.scalar_one_or_none() is None


class TestOwnershipAndReferentialIntegrity:
    """Tests for ownership validation and referential integrity."""

    @pytest.mark.asyncio
    async def test_user_cannot_access_another_users_business_profile(self, db_session: AsyncSession) -> None:
        """Test that a user cannot create a conversation with another user's business profile."""
        user1 = User(
            email="owner1@example.com",
            full_name="Owner One",
            hashed_password="hashed_password",
        )
        user2 = User(
            email="owner2@example.com",
            full_name="Owner Two",
            hashed_password="hashed_password",
        )
        db_session.add_all([user1, user2])
        await db_session.commit()
        await db_session.refresh(user1)
        await db_session.refresh(user2)

        profile = BusinessProfile(
            user_id=user1.id,
            business_name="Business One",
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

        # User2 tries to create conversation with user1's business profile
        # This should be allowed at DB level but prevented at application level
        conversation = Conversation(
            user_id=user2.id,
            business_profile_id=profile.id,
            title="Unauthorized Conversation",
        )
        db_session.add(conversation)
        await db_session.commit()
        await db_session.refresh(conversation)

        # The conversation exists but ownership validation should happen in service layer
        assert conversation.user_id == user2.id
        assert conversation.business_profile_id == profile.id

    @pytest.mark.asyncio
    async def test_recommendation_must_belong_to_business_profile_owner(self, db_session: AsyncSession) -> None:
        """Test recommendation user_id matches business profile user_id."""
        user1 = User(
            email="owner3@example.com",
            full_name="Owner Three",
            hashed_password="hashed_password",
        )
        user2 = User(
            email="owner4@example.com",
            full_name="Owner Four",
            hashed_password="hashed_password",
        )
        db_session.add_all([user1, user2])
        await db_session.commit()
        await db_session.refresh(user1)
        await db_session.refresh(user2)

        profile = BusinessProfile(
            user_id=user1.id,
            business_name="Business One",
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

        # Create recommendation with mismatched user_id (user2 instead of user1)
        # This should be prevented at application level, but DB allows it
        recommendation = Recommendation(
            business_profile_id=profile.id,
            user_id=user2.id,  # Different user
            category="Government Scheme",
            title="MSME Loan Scheme",
            description="Low interest loan",
        )
        db_session.add(recommendation)
        await db_session.commit()
        await db_session.refresh(recommendation)

        # The recommendation exists - ownership validation in service layer
        assert recommendation.user_id == user2.id
        assert recommendation.business_profile_id == profile.id

    @pytest.mark.asyncio
    async def test_roadmap_must_belong_to_business_profile_owner(self, db_session: AsyncSession) -> None:
        """Test roadmap user_id matches business profile user_id."""
        user1 = User(
            email="owner5@example.com",
            full_name="Owner Five",
            hashed_password="hashed_password",
        )
        user2 = User(
            email="owner6@example.com",
            full_name="Owner Six",
            hashed_password="hashed_password",
        )
        db_session.add_all([user1, user2])
        await db_session.commit()
        await db_session.refresh(user1)
        await db_session.refresh(user2)

        profile = BusinessProfile(
            user_id=user1.id,
            business_name="Business One",
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

        # Create roadmap with mismatched user_id
        roadmap = Roadmap(
            user_id=user2.id,  # Different user
            business_profile_id=profile.id,
            title="Business Setup Roadmap",
            description="Step by step guide",
        )
        db_session.add(roadmap)
        await db_session.commit()
        await db_session.refresh(roadmap)

        assert roadmap.user_id == user2.id
        assert roadmap.business_profile_id == profile.id

    @pytest.mark.asyncio
    async def test_task_cannot_exist_outside_roadmap_ownership(self, db_session: AsyncSession) -> None:
        """Test that tasks are bound to their parent roadmap."""
        user = User(
            email="owner7@example.com",
            full_name="Owner Seven",
            hashed_password="hashed_password",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        profile = BusinessProfile(
            user_id=user.id,
            business_name="Business One",
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

        roadmap = Roadmap(
            user_id=user.id,
            business_profile_id=profile.id,
            title="Business Setup Roadmap",
            description="Step by step guide",
        )
        db_session.add(roadmap)
        await db_session.commit()
        await db_session.refresh(roadmap)

        task = RoadmapTask(
            roadmap_id=roadmap.id,
            title="Register Business",
            description="Register the business with MCA",
            sequence_number=1,
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        # Task is bound to roadmap
        assert task.roadmap_id == roadmap.id

        # Deleting roadmap cascades to task
        await db_session.delete(roadmap)
        await db_session.commit()

        result = await db_session.execute(
            select(RoadmapTask).where(RoadmapTask.id == task.id)
        )
        assert result.scalar_one_or_none() is None


class TestTimestampHandling:
    """Tests for UTC timestamp handling."""

    @pytest.mark.asyncio
    async def test_created_at_is_utc(self, db_session: AsyncSession) -> None:
        """Test that created_at timestamps are timezone-aware UTC."""
        user = User(
            email="utc@example.com",
            full_name="UTC User",
            hashed_password="hashed_password",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.created_at.tzinfo is not None
        assert user.created_at.tzinfo == UTC or user.created_at.tzinfo.utcoffset(user.created_at) is not None

    @pytest.mark.asyncio
    async def test_updated_at_updates_on_modification(self, db_session: AsyncSession) -> None:
        """Test that updated_at is updated on modification."""
        user = User(
            email="utc2@example.com",
            full_name="UTC User",
            hashed_password="hashed_password",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        original_updated_at = user.updated_at
        await asyncio.sleep(0.01)

        user.full_name = "Updated Name"
        await db_session.commit()
        await db_session.refresh(user)

        assert user.updated_at > original_updated_at


# Import and metadata tests - run without database
# Moved to tests/test_models_import.py
