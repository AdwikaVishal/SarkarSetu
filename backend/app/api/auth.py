"""Authentication API router."""
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_auth_service, get_current_active_user
from app.models.user import User
from app.schemas.auth import (
    LogoutResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    TokenResponse,
    UserLogin,
    UserMeResponse,
    UserRegister,
    UserResponse,
)
from app.services.auth_service import (
    AccountInactiveError,
    AuthenticationError,
    AuthService,
    InvalidCredentialsError,
    TokenError,
    TokenRevokedError,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Register a new user account and return access/refresh tokens.",
)
async def register(
    user_data: UserRegister,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """
    Register a new user.

    - **email**: User's email address (must be unique)
    - **full_name**: User's full name (optional)
    - **password**: User's password (min 12 chars, must contain upper, lower, digit, special char)

    Returns access token, refresh token, and user info.
    """
    try:
        user = await auth_service.register(
            email=user_data.email,
            full_name=user_data.full_name,
            password=user_data.password,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from None
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from None

    access_token, refresh_token = await auth_service.create_tokens(user)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=30 * 60,  # 30 minutes
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login with email and password",
    description="Authenticate user and return access/refresh tokens.",
)
async def login(
    credentials: UserLogin,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """
    Login with email and password.

    - **email**: Registered email address
    - **password**: Account password

    Returns access token, refresh token, and user info.
    """
    try:
        user = await auth_service.authenticate(
            email=credentials.email,
            password=credentials.password,
        )
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        ) from None
    except AccountInactiveError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated",
        ) from None

    access_token, refresh_token = await auth_service.create_tokens(user)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=30 * 60,  # 30 minutes
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    summary="Refresh access and refresh tokens",
    description="Use refresh token to get new access and refresh tokens (rotation).",
)
async def refresh_tokens(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> RefreshTokenResponse:
    """
    Refresh access and refresh tokens.

    - **refresh_token**: Valid refresh token

    Returns new access token and rotated refresh token.
    """
    try:
        access_token, refresh_token = await auth_service.refresh_tokens(
            refresh_token=request.refresh_token,
        )
    except TokenRevokedError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token reuse detected - all sessions revoked for security",
        ) from None
    except TokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        ) from None

    return RefreshTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=30 * 60,  # 30 minutes
    )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Logout and revoke refresh token",
    description="Revoke the current refresh token.",
)
async def logout(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> LogoutResponse:
    """
    Logout and revoke the refresh token.

    - **refresh_token**: Refresh token to revoke
    """
    await auth_service.logout(request.refresh_token)
    return LogoutResponse(message="Successfully logged out")


@router.get(
    "/me",
    response_model=UserMeResponse,
    summary="Get current authenticated user",
    description="Return the currently authenticated user's information.",
)
async def get_me(
    current_user: User = Depends(get_current_active_user),
) -> UserMeResponse:
    """
    Get current authenticated user information.

    Returns user profile without sensitive data.
    """
    return UserMeResponse.model_validate(current_user)
