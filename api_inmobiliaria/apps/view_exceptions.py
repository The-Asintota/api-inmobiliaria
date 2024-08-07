from django.http.request import HttpRequest
from rest_framework import status
from typing import Any, Dict


class ViewException(Exception):
    """
    Base class for exceptions raised in views.
    """

    default_status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(
        self,
        request: HttpRequest,
        template_name: str,
        context: Dict[str, Any],
        status_code: int = None,
    ) -> None:
        """
        Initializes the exception during the execution of a view with the given
        parameters.
        """

        self.status_code = status_code or self.default_status_code
        self.request = request
        self.template_name = template_name
        self.context = context


class ResourceNotFoundViewError(ViewException):
    """
    An exception that is raised when a requested resource is not found.
    """

    default_status_code = status.HTTP_404_NOT_FOUND


class SendingViewError(ViewException):
    """
    An exception that is raised when an error occurs during the process of sending
    an email.
    """

    default_status_code = status.HTTP_503_SERVICE_UNAVAILABLE


class TokenViewError(ViewException):
    """
    Exception raised when an error occurs with a one-time use token.
    """

    default_status_code = status.HTTP_401_UNAUTHORIZED
