from rest_framework.exceptions import APIException as BaseAPIException
from rest_framework import status
from typing import Optional, Union, Dict, Any


class DetailDictMixin:
    """
    A mixin class that provides a method to build a detailed dictionary for the error.
    """

    default_detail: str
    default_code: str

    def __init__(
        self,
        detail: Union[Dict[str, Any], str, None] = None,
        code: Optional[str] = None,
    ) -> None:
        """
        Builds a detail dictionary for the error to give more information to API
        users.
        """

        detail_dict = {
            "detail": self.default_detail,
            "code": self.default_code,
        }
        if isinstance(detail, dict):
            detail_dict.update(detail)
        elif detail is not None:
            detail_dict["detail"] = detail
        if code is not None:
            detail_dict["code"] = code
        super().__init__(detail_dict)


class APIException(BaseAPIException, DetailDictMixin):
    """
    Base class for exceptions raised in API views.
    """

    def __init__(
        self, detail: str | Dict[str, Any] = None, code: str = None
    ) -> None:
        """
        Initializes the exception during the execution of a API view with the given
        parameters.
        """

        if isinstance(detail, dict):
            self.detail = {"detail": detail or self.default_detail}
        else:
            self.detail = detail or self.default_detail
        self.code = code or self.default_code
        super().__init__(detail=self.detail, code=self.code)


class AuthenticationFailedAPIError(APIException):
    """
    An exception that is raised when an authentication attempt fails.
    """

    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "Incorrect authentication credentials."
    default_code = "authentication_failed"


class AccountActivationAPIError(APIException):
    """
    An exception that is raised when an error occurs during the account activation process.
    """

    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "Error activating user account."
    default_code = "activation_error"


class DatabaseConnectionAPIError(APIException):
    """
    Exception raised when a connection to the database cannot be established.
    """

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Unable to establish a connection with the database. Please try again later."
    default_code = "database_connection_error"


class ResourceNotFoundAPIError(APIException):
    """
    Exception raised when a requested resource is not found.
    """

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "requested resource not found."
    default_code = "resource_not_found"


class JWTAPIError(APIException):
    """
    Exception raised when a token error occurs.
    """

    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "JWT error."
    default_code = "JWT_error"


class NotAuthenticatedAPIError(APIException):
    """
    Exception raised when the user is not authenticated.
    """

    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "Authentication credentials were not provided."
    default_code = "authentication_failed"


class PermissionDeniedAPIError(APIException):

    status_code = status.HTTP_403_FORBIDDEN
    default_detail = (
        "The user does not have permissions to perform this action."
    )
    default_code = "permission_denied"
