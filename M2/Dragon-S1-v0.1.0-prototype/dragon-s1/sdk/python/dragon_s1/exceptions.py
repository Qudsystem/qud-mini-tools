class DragonAPIError(Exception):
    """Base exception for Dragon S1 SDK."""
    pass

class AuthError(DragonAPIError):
    """Raised when authentication fails."""
    pass

class RegistrationError(DragonAPIError):
    """Raised when device registration fails."""
    pass
