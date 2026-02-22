"""
Custom exception classes for structured error handling.
Wrap risky logic in services and raise meaningful exceptions.
Do NOT expose raw tracebacks to Telegram users.
"""


class BotBaseError(Exception):
    """Base exception for all bot errors."""

    def __init__(self, message: str, *, original: Exception | None = None):
        super().__init__(message)
        self.original = original


class DatabaseError(BotBaseError):
    """Raised when a database operation fails."""


class BroadcastError(BotBaseError):
    """Raised when a broadcast operation fails (aggregate or fatal)."""

    def __init__(
        self,
        message: str,
        *,
        delivered: int = 0,
        failed: int = 0,
        blocked: int = 0,
        original: Exception | None = None,
    ):
        super().__init__(message, original=original)
        self.delivered = delivered
        self.failed = failed
        self.blocked = blocked


class WelcomeBuilderError(BotBaseError):
    """Raised when welcome message building or sending fails."""


class SchedulerError(BotBaseError):
    """Raised when a scheduled task fails."""


class ValidationError(BotBaseError):
    """Raised when input validation fails."""
