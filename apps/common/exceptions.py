from typing import Optional, Any

class ServiceException(Exception):
    """Base exception for service layer errors"""
    def __init__(self, message: str, details: Optional[Any] = None):
        self.message = message
        self.details = details
        super().__init__(message)

class InvalidInputError(ServiceException):
    """Invalid input data"""
    pass

class AuthorizationError(ServiceException):
    """User not authorized for action"""
    pass

class ResourceNotFoundError(ServiceException):
    """Requested resource not found"""
    pass
