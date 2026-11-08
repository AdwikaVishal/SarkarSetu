"""Business profile service layer."""
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.business import BusinessProfile
from app.schemas.business import BusinessProfileCreate, BusinessProfileUpdate
from app.services.ownership import OwnershipService, ResourceNotFoundError


class BusinessService:
    """Service for business profile operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.ownership = OwnershipService(db)

    async def create_business_profile(
        self,
        user_id: UUID,
        profile_data: BusinessProfileCreate,
    ) -> BusinessProfile:
        """Create a new business profile for a user.

        Args:
            user_id: ID of the user creating the profile.
            profile_data: Validated business profile data.

        Returns:
            The created business profile.

        Raises:
            ValueError: If validation fails.
        """
        profile = BusinessProfile(
            user_id=user_id,
            business_name=profile_data.business_name,
            business_type=profile_data.business_type,
            industry=profile_data.industry,
            state=profile_data.state,
            district=profile_data.district,
            annual_turnover=profile_data.annual_turnover,
            employee_count=profile_data.employee_count,
            sales_channels=profile_data.sales_channels,
            business_structure=profile_data.business_structure,
            business_stage=profile_data.business_stage,
            description=profile_data.description,
            city=profile_data.city,
            pincode=profile_data.pincode,
            udyam_number=profile_data.udyam_number,
            gstin=profile_data.gstin,
            website=profile_data.website,
            woman_owned=profile_data.woman_owned,
            social_category=profile_data.social_category,
            products_services=profile_data.products_services,
            operating_mode=profile_data.operating_mode,
            date_of_establishment=profile_data.date_of_establishment,
            is_default=False,
        )
        self.db.add(profile)
        await self.db.commit()
        await self.db.refresh(profile)
        return profile

    async def get_business_profile(
        self,
        user_id: UUID,
        business_profile_id: UUID,
        include_archived: bool = False,
    ) -> BusinessProfile:
        """Get a business profile owned by the user.

        Args:
            user_id: ID of the authenticated user.
            business_profile_id: ID of the business profile.
            include_archived: Whether to include archived profiles.

        Returns:
            The business profile if owned by the user.

        Raises:
            ResourceNotFoundError: If profile not found or not owned by user.
        """
        if include_archived:
            return await self.ownership.get_user_business_profile_or_archived(
                user_id, business_profile_id
            )
        return await self.ownership.get_user_business_profile(
            user_id, business_profile_id
        )

    async def list_business_profiles(
        self,
        user_id: UUID,
    ) -> list[BusinessProfile]:
        """List all active (non-archived) business profiles for a user.

        Args:
            user_id: ID of the authenticated user.

        Returns:
            List of active business profiles owned by the user.
        """
        return await self.ownership.list_user_business_profiles(user_id)

    async def update_business_profile(
        self,
        user_id: UUID,
        business_profile_id: UUID,
        update_data: BusinessProfileUpdate,
    ) -> BusinessProfile:
        """Update a business profile owned by the user.

        Args:
            user_id: ID of the authenticated user.
            business_profile_id: ID of the business profile.
            update_data: Fields to update (partial update supported).

        Returns:
            The updated business profile.

        Raises:
            ResourceNotFoundError: If profile not found or not owned by user.
        """
        profile = await self.get_business_profile(user_id, business_profile_id)

        # Prevent updating server-controlled fields
        update_dict = update_data.model_dump(exclude_unset=True)
        protected_fields = {"id", "user_id", "is_deleted", "deleted_at", "created_at", "updated_at", "is_default"}
        for field in protected_fields:
            update_dict.pop(field, None)

        for key, value in update_dict.items():
            setattr(profile, key, value)

        await self.db.commit()
        await self.db.refresh(profile)
        return profile

    async def archive_business_profile(
        self,
        user_id: UUID,
        business_profile_id: UUID,
    ) -> BusinessProfile:
        """Archive (soft-delete) a business profile.

        Setting is_deleted=true and deleted_at prevents the profile from
        being used in new workflows while preserving historical records.

        Args:
            user_id: ID of the authenticated user.
            business_profile_id: ID of the business profile.

        Returns:
            The archived business profile.

        Raises:
            ResourceNotFoundError: If profile not found or not owned by user.
        """
        profile = await self.get_business_profile(user_id, business_profile_id)

        if profile.is_deleted:
            return profile  # Already archived, idempotent

        profile.is_deleted = True
        profile.deleted_at = datetime.now(UTC)
        profile.is_default = False  # Archived profile cannot be default

        await self.db.commit()
        await self.db.refresh(profile)
        return profile

    async def restore_business_profile(
        self,
        user_id: UUID,
        business_profile_id: UUID,
    ) -> BusinessProfile:
        """Restore an archived business profile.

        Args:
            user_id: ID of the authenticated user.
            business_profile_id: ID of the business profile.

        Returns:
            The restored business profile.

        Raises:
            ResourceNotFoundError: If profile not found or not owned by user.
        """
        profile = await self.get_business_profile(
            user_id, business_profile_id, include_archived=True
        )

        if not profile.is_deleted:
            return profile  # Already active, idempotent

        profile.is_deleted = False
        profile.deleted_at = None

        await self.db.commit()
        await self.db.refresh(profile)
        return profile

    async def list_archived_business_profiles(
        self,
        user_id: UUID,
    ) -> list[BusinessProfile]:
        """List all archived business profiles for a user.

        Args:
            user_id: ID of the authenticated user.

        Returns:
            List of archived business profiles owned by the user.
        """
        result = await self.db.execute(
            select(BusinessProfile).where(
                BusinessProfile.user_id == user_id,
                BusinessProfile.is_deleted == True,  # noqa: E712
            ).order_by(BusinessProfile.deleted_at.desc())
        )
        return list(result.scalars().all())

    async def set_default_business_profile(
        self,
        user_id: UUID,
        business_profile_id: UUID,
    ) -> BusinessProfile:
        """Set a business profile as the user's default.

        Only one profile per user can be the default. Setting a new default
        unsets any existing default. Archived profiles cannot be set as default.

        Args:
            user_id: ID of the authenticated user.
            business_profile_id: ID of the business profile.

        Returns:
            The business profile set as default.

        Raises:
            ResourceNotFoundError: If profile not found, not owned by user,
                or is archived.
        """
        profile = await self.get_business_profile(user_id, business_profile_id)

        if profile.is_deleted:
            raise ResourceNotFoundError(
                "Archived business profile cannot be set as default"
            )

        # Unset any existing default profile for this user
        result = await self.db.execute(
            select(BusinessProfile).where(
                BusinessProfile.user_id == user_id,
                BusinessProfile.is_default == True,  # noqa: E712
                BusinessProfile.id != business_profile_id,
            )
        )
        current_defaults = result.scalars().all()
        for default_profile in current_defaults:
            default_profile.is_default = False

        # Set the new default
        profile.is_default = True

        await self.db.commit()
        await self.db.refresh(profile)
        return profile

    async def get_default_business_profile(
        self,
        user_id: UUID,
    ) -> BusinessProfile | None:
        """Get the user's default business profile.

        Args:
            user_id: ID of the authenticated user.

        Returns:
            The default business profile, or None if none set.
        """
        result = await self.db.execute(
            select(BusinessProfile).where(
                BusinessProfile.user_id == user_id,
                BusinessProfile.is_default == True,  # noqa: E712
                BusinessProfile.is_deleted == False,  # noqa: E712
            )
        )
        return result.scalar_one_or_none()
