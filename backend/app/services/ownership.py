"""Ownership validation services for user resources."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    BusinessProfile,
    Conversation,
    EligibilityResult,
    Message,
    Recommendation,
    Roadmap,
    RoadmapTask,
    UploadedDocument,
)


class OwnershipError(Exception):
    """Raised when ownership validation fails."""
    pass


class ResourceNotFoundError(OwnershipError):
    """Raised when resource is not found or not accessible."""
    pass


class ForbiddenAccessError(OwnershipError):
    """Raised when user tries to access another user's resource."""
    pass


class OwnershipService:
    """Service for validating resource ownership."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # BusinessProfile ownership

    async def get_user_business_profile(
        self,
        user_id: UUID,
        business_profile_id: UUID,
    ) -> BusinessProfile:
        """
        Get a business profile owned by the user.

        Args:
            user_id: User ID.
            business_profile_id: Business profile ID.

        Returns:
            Business profile if owned by user.

        Raises:
            ResourceNotFoundError: If not found or not owned by user.
        """
        result = await self.db.execute(
            select(BusinessProfile).where(
                BusinessProfile.id == business_profile_id,
                BusinessProfile.user_id == user_id,
                BusinessProfile.is_deleted == False,  # noqa: E712
            )
        )
        profile = result.scalar_one_or_none()
        if not profile:
            raise ResourceNotFoundError("Business profile not found")
        return profile

    async def get_user_business_profile_or_archived(
        self,
        user_id: UUID,
        business_profile_id: UUID,
    ) -> BusinessProfile:
        """
        Get a business profile owned by the user (including archived).

        Args:
            user_id: User ID.
            business_profile_id: Business profile ID.

        Returns:
            Business profile if owned by user.

        Raises:
            ResourceNotFoundError: If not found or not owned by user.
        """
        result = await self.db.execute(
            select(BusinessProfile).where(
                BusinessProfile.id == business_profile_id,
                BusinessProfile.user_id == user_id,
            )
        )
        profile = result.scalar_one_or_none()
        if not profile:
            raise ResourceNotFoundError("Business profile not found")
        return profile

    async def list_user_business_profiles(self, user_id: UUID) -> list[BusinessProfile]:
        """
        List all non-deleted business profiles for a user.

        Args:
            user_id: User ID.

        Returns:
            List of business profiles.
        """
        result = await self.db.execute(
            select(BusinessProfile).where(
                BusinessProfile.user_id == user_id,
                BusinessProfile.is_deleted == False,  # noqa: E712
            ).order_by(BusinessProfile.created_at.desc())
        )
        return list(result.scalars().all())

    # Conversation ownership

    async def get_user_conversation(
        self,
        user_id: UUID,
        conversation_id: UUID,
    ) -> Conversation:
        """
        Get a conversation owned by the user.

        Args:
            user_id: User ID.
            conversation_id: Conversation ID.

        Returns:
            Conversation if owned by user.

        Raises:
            ResourceNotFoundError: If not found or not owned by user.
        """
        result = await self.db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise ResourceNotFoundError("Conversation not found")
        return conversation

    async def validate_conversation_business_profile(
        self,
        user_id: UUID,
        business_profile_id: UUID,
    ) -> BusinessProfile:
        """
        Validate that a business profile belongs to the user before creating a conversation.

        Args:
            user_id: User ID.
            business_profile_id: Business profile ID.

        Returns:
            Business profile if owned by user.

        Raises:
            ResourceNotFoundError: If not found or not owned by user.
        """
        return await self.get_user_business_profile(user_id, business_profile_id)

    # Message ownership (via conversation)

    async def get_user_message(
        self,
        user_id: UUID,
        message_id: UUID,
    ) -> Message:
        """
        Get a message from a conversation owned by the user.

        Args:
            user_id: User ID.
            message_id: Message ID.

        Returns:
            Message if owned by user.

        Raises:
            ResourceNotFoundError: If not found or not owned by user.
        """
        result = await self.db.execute(
            select(Message)
            .join(Conversation)
            .where(
                Message.id == message_id,
                Conversation.user_id == user_id,
            )
        )
        message = result.scalar_one_or_none()
        if not message:
            raise ResourceNotFoundError("Message not found")
        return message

    # Recommendation ownership

    async def get_user_recommendation(
        self,
        user_id: UUID,
        recommendation_id: UUID,
    ) -> Recommendation:
        """
        Get a recommendation owned by the user.

        Args:
            user_id: User ID.
            recommendation_id: Recommendation ID.

        Returns:
            Recommendation if owned by user.

        Raises:
            ResourceNotFoundError: If not found or not owned by user.
        """
        result = await self.db.execute(
            select(Recommendation).where(
                Recommendation.id == recommendation_id,
                Recommendation.user_id == user_id,
            )
        )
        recommendation = result.scalar_one_or_none()
        if not recommendation:
            raise ResourceNotFoundError("Recommendation not found")
        return recommendation

    async def validate_recommendation_business_profile(
        self,
        user_id: UUID,
        business_profile_id: UUID,
    ) -> BusinessProfile:
        """
        Validate that a business profile belongs to the user before creating a recommendation.

        Args:
            user_id: User ID.
            business_profile_id: Business profile ID.

        Returns:
            Business profile if owned by user.

        Raises:
            ResourceNotFoundError: If not found or not owned by user.
        """
        return await self.get_user_business_profile(user_id, business_profile_id)

    # EligibilityResult ownership

    async def get_user_eligibility_result(
        self,
        user_id: UUID,
        eligibility_result_id: UUID,
    ) -> EligibilityResult:
        """
        Get an eligibility result owned by the user.

        Args:
            user_id: User ID.
            eligibility_result_id: Eligibility result ID.

        Returns:
            Eligibility result if owned by user.

        Raises:
            ResourceNotFoundError: If not found or not owned by user.
        """
        result = await self.db.execute(
            select(EligibilityResult).where(
                EligibilityResult.id == eligibility_result_id,
                EligibilityResult.user_id == user_id,
            )
        )
        eligibility = result.scalar_one_or_none()
        if not eligibility:
            raise ResourceNotFoundError("Eligibility result not found")
        return eligibility

    async def validate_eligibility_business_profile(
        self,
        user_id: UUID,
        business_profile_id: UUID,
    ) -> BusinessProfile:
        """
        Validate that a business profile belongs to the user before creating an eligibility result.

        Args:
            user_id: User ID.
            business_profile_id: Business profile ID.

        Returns:
            Business profile if owned by user.

        Raises:
            ResourceNotFoundError: If not found or not owned by user.
        """
        return await self.get_user_business_profile(user_id, business_profile_id)

    # Roadmap ownership

    async def get_user_roadmap(
        self,
        user_id: UUID,
        roadmap_id: UUID,
    ) -> Roadmap:
        """
        Get a roadmap owned by the user.

        Args:
            user_id: User ID.
            roadmap_id: Roadmap ID.

        Returns:
            Roadmap if owned by user.

        Raises:
            ResourceNotFoundError: If not found or not owned by user.
        """
        result = await self.db.execute(
            select(Roadmap).where(
                Roadmap.id == roadmap_id,
                Roadmap.user_id == user_id,
            )
        )
        roadmap = result.scalar_one_or_none()
        if not roadmap:
            raise ResourceNotFoundError("Roadmap not found")
        return roadmap

    async def validate_roadmap_business_profile(
        self,
        user_id: UUID,
        business_profile_id: UUID,
    ) -> BusinessProfile:
        """
        Validate that a business profile belongs to the user before creating a roadmap.

        Args:
            user_id: User ID.
            business_profile_id: Business profile ID.

        Returns:
            Business profile if owned by user.

        Raises:
            ResourceNotFoundError: If not found or not owned by user.
        """
        return await self.get_user_business_profile(user_id, business_profile_id)

    # RoadmapTask ownership (via roadmap)

    async def get_user_roadmap_task(
        self,
        user_id: UUID,
        task_id: UUID,
    ) -> RoadmapTask:
        """
        Get a roadmap task from a roadmap owned by the user.

        Args:
            user_id: User ID.
            task_id: Task ID.

        Returns:
            Task if owned by user.

        Raises:
            ResourceNotFoundError: If not found or not owned by user.
        """
        result = await self.db.execute(
            select(RoadmapTask)
            .join(Roadmap)
            .where(
                RoadmapTask.id == task_id,
                Roadmap.user_id == user_id,
            )
        )
        task = result.scalar_one_or_none()
        if not task:
            raise ResourceNotFoundError("Roadmap task not found")
        return task

    # UploadedDocument ownership

    async def get_user_uploaded_document(
        self,
        user_id: UUID,
        document_id: UUID,
    ) -> UploadedDocument:
        """
        Get an uploaded document owned by the user.

        Args:
            user_id: User ID.
            document_id: Document ID.

        Returns:
            Document if owned by user.

        Raises:
            ResourceNotFoundError: If not found or not owned by user.
        """
        result = await self.db.execute(
            select(UploadedDocument).where(
                UploadedDocument.id == document_id,
                UploadedDocument.user_id == user_id,
            )
        )
        document = result.scalar_one_or_none()
        if not document:
            raise ResourceNotFoundError("Document not found")
        return document

    async def validate_document_business_profile(
        self,
        user_id: UUID,
        business_profile_id: UUID | None,
    ) -> BusinessProfile | None:
        """
        Validate that a business profile belongs to the user (if provided).

        Args:
            user_id: User ID.
            business_profile_id: Optional business profile ID.

        Returns:
            Business profile if provided and owned by user, None if not provided.

        Raises:
            ResourceNotFoundError: If provided but not found or not owned by user.
        """
        if business_profile_id is None:
            return None
        return await self.get_user_business_profile(user_id, business_profile_id)
