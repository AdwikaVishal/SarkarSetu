"""Business profile API router."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.database.connection import get_db
from app.models.user import User
from app.schemas.business import (
    BusinessProfileCreate,
    BusinessProfileListResponse,
    BusinessProfileResponse,
    BusinessProfileUpdate,
)
from app.services.auth_service import AuthService
from app.services.business_service import BusinessService
from app.services.ownership import ResourceNotFoundError

router = APIRouter(prefix="/businesses", tags=["business-profiles"])


async def get_business_service(
    db: AsyncSession = Depends(get_db),
) -> BusinessService:
    """Dependency to get BusinessService instance."""
    return BusinessService(db)


async def get_auth_service(
    db: AsyncSession = Depends(get_db),
) -> AuthService:
    """Dependency to get AuthService instance."""
    return AuthService(db)


@router.post(
    "/",
    response_model=BusinessProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create business profile",
    description="Create a new business profile for the authenticated user.",
)
async def create_business_profile(
    profile_data: BusinessProfileCreate,
    business_service: BusinessService = Depends(get_business_service),
    current_user: User = Depends(get_current_active_user),
) -> BusinessProfileResponse:
    """Create a new business profile.

    Creates a business profile owned by the authenticated user.
    """
    profile = await business_service.create_business_profile(
        user_id=current_user.id,
        profile_data=profile_data,
    )
    return BusinessProfileResponse.model_validate(profile)


@router.get(
    "/archived",
    response_model=BusinessProfileListResponse,
    summary="List archived business profiles",
    description="List all archived business profiles for the authenticated user.",
)
async def list_archived_business_profiles(
    business_service: BusinessService = Depends(get_business_service),
    current_user: User = Depends(get_current_active_user),
) -> BusinessProfileListResponse:
    """List all archived business profiles for the authenticated user."""
    profiles = await business_service.list_archived_business_profiles(
        user_id=current_user.id
    )
    return BusinessProfileListResponse(
        items=[BusinessProfileResponse.model_validate(p) for p in profiles],
        total=len(profiles),
    )


@router.get(
    "/",
    response_model=BusinessProfileListResponse,
    summary="List business profiles",
    description="List all active (non-archived) business profiles for the user.",
)
async def list_business_profiles(
    business_service: BusinessService = Depends(get_business_service),
    current_user: User = Depends(get_current_active_user),
) -> BusinessProfileListResponse:
    """List all active business profiles for the authenticated user."""
    profiles = await business_service.list_business_profiles(
        user_id=current_user.id
    )
    return BusinessProfileListResponse(
        items=[BusinessProfileResponse.model_validate(p) for p in profiles],
        total=len(profiles),
    )


@router.get(
    "/{business_id}",
    response_model=BusinessProfileResponse,
    summary="Get business profile",
    description="Retrieve a specific business profile owned by the user.",
)
async def get_business_profile(
    business_id: str,
    business_service: BusinessService = Depends(get_business_service),
    current_user: User = Depends(get_current_active_user),
) -> BusinessProfileResponse:
    """Get a business profile by ID, owned by the current user."""
    try:
        profile_id = UUID(business_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid business profile ID format",
        ) from None

    try:
        profile = await business_service.get_business_profile(
            user_id=current_user.id,
            business_profile_id=profile_id,
        )
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found",
        ) from None
    return BusinessProfileResponse.model_validate(profile)


@router.patch(
    "/{business_id}",
    response_model=BusinessProfileResponse,
    summary="Update business profile",
    description="Partially update a business profile owned by the user.",
)
async def update_business_profile(
    business_id: str,
    update_data: BusinessProfileUpdate,
    business_service: BusinessService = Depends(get_business_service),
    current_user: User = Depends(get_current_active_user),
) -> BusinessProfileResponse:
    """Partially update a business profile owned by the current user."""
    try:
        profile_id = UUID(business_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid business profile ID format",
        ) from None

    try:
        profile = await business_service.update_business_profile(
            user_id=current_user.id,
            business_profile_id=profile_id,
            update_data=update_data,
        )
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found",
        ) from None
    return BusinessProfileResponse.model_validate(profile)


@router.delete(
    "/{business_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Archive business profile",
    description="Soft-delete (archive) a business profile. Historical records are preserved.",
)
async def archive_business_profile(
    business_id: str,
    business_service: BusinessService = Depends(get_business_service),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """Archive (soft-delete) a business profile owned by the current user."""
    try:
        profile_id = UUID(business_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid business profile ID format",
        ) from None

    try:
        await business_service.archive_business_profile(
            user_id=current_user.id,
            business_profile_id=profile_id,
        )
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found",
        ) from None


@router.post(
    "/{business_id}/restore",
    response_model=BusinessProfileResponse,
    summary="Restore archived business profile",
    description="Restore an archived business profile owned by the user.",
)
async def restore_business_profile(
    business_id: str,
    business_service: BusinessService = Depends(get_business_service),
    current_user: User = Depends(get_current_active_user),
) -> BusinessProfileResponse:
    """Restore an archived business profile owned by the current user."""
    try:
        profile_id = UUID(business_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid business profile ID format",
        ) from None

    try:
        profile = await business_service.restore_business_profile(
            user_id=current_user.id,
            business_profile_id=profile_id,
        )
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found",
        ) from None
    return BusinessProfileResponse.model_validate(profile)


@router.patch(
    "/{business_id}/default",
    response_model=BusinessProfileResponse,
    summary="Set default business profile",
    description="Set a business profile as the user's default. Only one default per user.",
)
async def set_default_business_profile(
    business_id: str,
    business_service: BusinessService = Depends(get_business_service),
    current_user: User = Depends(get_current_active_user),
) -> BusinessProfileResponse:
    """Set a business profile as the default for the current user."""
    try:
        profile_id = UUID(business_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid business profile ID format",
        ) from None

    try:
        profile = await business_service.set_default_business_profile(
            user_id=current_user.id,
            business_profile_id=profile_id,
        )
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found",
        ) from None
    return BusinessProfileResponse.model_validate(profile)
