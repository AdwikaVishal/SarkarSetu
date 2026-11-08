"""Context builder for intent classification.

Builds context from user messages, conversation history, business profiles,
and rule sets for intent classification and entity extraction.
"""


from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.business import BusinessProfile
from app.models.message import Message

MAX_CONVERSATION_HISTORY = 10
MAX_MESSAGE_LENGTH = 5000


async def get_conversation_history(
    db: AsyncSession,
    conversation_id: str,
    limit: int = MAX_CONVERSATION_HISTORY,
) -> list[dict[str, str]]:
    """Get recent conversation history for context.

    Args:
        db: Database session.
        conversation_id: ID of the conversation.
        limit: Maximum number of messages to retrieve.

    Returns:
        List of message dicts with role and content.
    """
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    messages = result.scalars().all()

    return [
        {"role": m.role, "content": m.content}
        for m in reversed(messages)
    ]


async def get_business_context(
    db: AsyncSession,
    user_id: str,
    business_profile_id: str | None = None,
) -> dict[str, str | None] | None:
    """Get business context for intent classification.

    Args:
        db: Database session.
        user_id: ID of the authenticated user.
        business_profile_id: Optional business profile ID.

    Returns:
        Dictionary with business context or None if not provided.

    Raises:
        ValueError: If business profile not found or not owned by user.
    """
    if business_profile_id is None:
        return None

    result = await db.execute(
        select(BusinessProfile).where(
            BusinessProfile.id == business_profile_id,
            BusinessProfile.user_id == user_id,
            BusinessProfile.is_deleted == False,  # noqa: E712
        )
    )
    profile = result.scalar_one_or_none()

    if profile is None:
        return None

    return {
        "business_name": profile.business_name,
        "business_type": profile.business_type,
        "industry": profile.industry,
        "state": profile.state,
        "district": profile.district,
        "annual_turnover": str(profile.annual_turnover)
        if profile.annual_turnover
        else None,
        "employee_count": str(profile.employee_count)
        if profile.employee_count
        else None,
        "business_stage": profile.business_stage,
    }


def build_conversation_context(
    messages: list[dict[str, str]],
) -> str:
    """Build conversation context string from message history.

    Args:
        messages: List of message dicts with role and content.

    Returns:
        Formatted conversation context string.
    """
    if not messages:
        return ""

    lines = ["Previous conversation:"]
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        lines.append(f"{role.capitalize()}: {content}")

    return "\n".join(lines)


def build_business_context(
    business_profile: dict[str, str] | None,
) -> str:
    """Build business context string from profile data.

    Args:
        business_profile: Business profile dictionary or None.

    Returns:
        Formatted business context string.
    """
    if not business_profile:
        return ""

    lines = ["Business context:"]
    for key, value in business_profile.items():
        if value is not None:
            lines.append(f"{key.replace('_', ' ').title()}: {value}")

    return "\n".join(lines)


def sanitize_message(message: str) -> str:
    """Sanitize user message for safe processing.

    Strips leading/trailing whitespace and limits length.

    Args:
        message: Raw user message.

    Returns:
        Sanitized message string.
    """
    return message.strip()[:MAX_MESSAGE_LENGTH]


def detect_language(message: str) -> str:
    """Simple language detection for user message.

    Detects English, Hindi, Kannada, Hinglish, or mixed language.
    This is a heuristic-based detector.

    Args:
        message: User message text.

    Returns:
        Language code string.
    """
    # Check for Devanagari script (Hindi, Marathi, etc.)
    devanagari_chars = sum(
        1 for ch in message if "\u0900" <= ch <= "\u097F"
    )
    # Check for Kannada script
    kannada_chars = sum(
        1 for ch in message if "\u0C80" <= ch <= "\u0CFF"
    )

    total_chars = len([c for c in message if c.isalpha()])

    if total_chars == 0:
        return "unknown"

    devanagari_ratio = devanagari_chars / total_chars
    kannada_ratio = kannada_chars / total_chars

    if kannada_ratio > 0.3:
        return "kn"
    elif devanagari_ratio > 0.3:
        return "hi"
    elif devanagari_ratio > 0.1:
        return "en-hi"  # Hinglish
    else:
        return "en"


def is_short_response(message: str) -> bool:
    """Check if message is a short affirmative/negative response.

    Args:
        message: User message text.

    Returns:
        True if message is a short yes/no type response.
    """
    stripped = message.strip().lower()
    short_responses = {
        "yes", "no", "y", "n", "yeah", "nah", "sure", "okay", "ok",
        "ha", "nahi", "haan", "ji", "theek", "chalega", "chalta hai",
    }
    return stripped in short_responses or len(stripped) <= 3


def is_greeting(message: str) -> bool:
    """Check if message is a greeting.

    Args:
        message: User message text.

    Returns:
        True if message appears to be a greeting.
    """
    stripped = message.strip().lower()
    greetings = {
        "hello", "hi", "hey", "hiya", "howdy", "greetings",
        "namaste", "namaskar", "vanakkam", "sat sri akal",
        "good morning", "good afternoon", "good evening",
        "good morning!", "good afternoon!", "good evening!",
        "hi there", "hello there", "hey there",
    }
    return stripped in greetings


def is_unsupported_request(message: str) -> bool:
    """Check if message is clearly outside supported scope.

    Args:
        message: User message text.

    Returns:
        True if message appears to be out of scope.
    """
    stripped = message.strip().lower()
    # Simple heuristic - very short messages or obvious non-business queries
    if len(stripped) < 3:
        return True
    return False
