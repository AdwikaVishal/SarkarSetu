"""AI service exceptions.

Defines application-level exceptions for AI-related errors.
These map to appropriate HTTP status codes in the API layer.
"""


class AIError(Exception):
    """Base exception for AI service errors."""

    def __init__(self, message: str, status_code: int = 500) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class AIServiceUnavailableError(AIError):
    """Raised when AI functionality is not available or configured."""

    def __init__(self, message: str = "AI service is not available") -> None:
        super().__init__(message, status_code=503)


class AIAuthenticationError(AIError):
    """Raised when AI API key is invalid or authentication fails."""

    def __init__(self, message: str = "AI service authentication failed") -> None:
        super().__init__(message, status_code=401)


class AIRateLimitError(AIError):
    """Raised when AI provider rate limit is exceeded."""

    def __init__(self, message: str = "AI service rate limit exceeded") -> None:
        super().__init__(message, status_code=429)


class AITimeoutError(AIError):
    """Raised when AI provider request times out."""

    def __init__(self, message: str = "AI service request timed out") -> None:
        super().__init__(message, status_code=504)


class AIProviderError(AIError):
    """Raised when AI provider returns an error."""

    def __init__(self, message: str = "AI provider error") -> None:
        super().__init__(message, status_code=502)


class AIResponseValidationError(AIError):
    """Raised when AI model response fails validation."""

    def __init__(self, message: str = "AI response validation failed") -> None:
        super().__init__(message, status_code=502)
