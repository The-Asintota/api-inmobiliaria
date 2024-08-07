from apps.api_exceptions import (
    NotAuthenticatedAPIError,
    PermissionDeniedAPIError,
)
from rest_framework.serializers import Serializer
from rest_framework.request import Request
from rest_framework import permissions, generics
from typing import List, Callable


class MethodHTTPMapped:
    """
    A class that maps HTTP methods to specific application classes, authentication
    classes, permission classes, and serializers.

    This class configures a view so that it can have different behavior based on
    the HTTP method of the request. For example, you might want to use different
    serializers for GET and POST requests, or apply different permissions for
    different methods.

    Any class that inherits from MethodHTTPMapped must also inherit from GenericAPIView.
    """

    application_class = None
    application_mapping = {}
    authentication_mapping = {}
    permission_mapping = {}
    serializer_mapping = {}
    status_code_mapping = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if not generics.GenericAPIView in cls.__bases__:
            raise TypeError(
                f"The {cls.__name__} class must inherit from generics.GenericAPIView. Make sure your view definition includes GenericAPIView as a base class when using the MethodHTTPMapped class."
            )

    def get_authenticators(self) -> List[Callable]:
        """
        Returns the authenticators that the view should use for the incoming request
        based on the HTTP method.
        """

        try:
            authentication_classes = self.authentication_mapping[
                self.request.method
            ]
        except (AttributeError, KeyError):
            return []

        return [auth() for auth in authentication_classes]

    def get_permissions(self) -> List[permissions.BasePermission]:
        """
        Returns the permission classes that the view should use for the incoming
        request based on the HTTP method.
        """

        try:
            permission_classes = self.permission_mapping[self.request.method]
        except (AttributeError, KeyError):
            return []

        return [permission() for permission in permission_classes]

    def get_serializer_class(self) -> Serializer:
        """
        Returns the serializer class that the view should use for the incoming
        request based on the HTTP method.
        """

        return self.serializer_mapping[self.request.method]

    def get_application_class(self) -> Callable:
        """
        Returns the application class that the view should use for the incoming
        request based on the HTTP method.
        """

        return self.application_mapping[self.request.method]

    def get_status_code(self) -> str:
        """
        Returns the status code that the view should use for the incoming request
        based on the HTTP method.
        """

        return self.status_code_mapping[self.request.method]

    def permission_denied(
        self, request: Request, message: str = None, code: str = None
    ) -> None:
        """
        If request is not permitted, determine what kind of exception to raise.

        #### Parameters:
        - request: The incoming request object.
        - message: The message to include in the exception.
        - code: The error code to include in the exception.
        """

        if request.authenticators and not request.successful_authenticator:
            raise NotAuthenticatedAPIError(code=code, detail=message)
        raise PermissionDeniedAPIError(code=code, detail=message)

    def check_permissions(self, request: Request) -> None:
        """
        Check if the request should be permitted. Raises an appropriate exception
        if the request is not permitted.

        #### Parameters:
        - request: The incoming request object.
        """

        for permission in self.get_permissions():
            if not permission.has_permission(request=request, view=self):
                self.permission_denied(
                    request=request,
                    message=getattr(permission, "message", None),
                    code=getattr(permission, "code", None),
                )
