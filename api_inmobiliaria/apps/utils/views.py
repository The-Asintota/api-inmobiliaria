from apps.api_exceptions import (
    NotAuthenticatedAPIError,
    PermissionDeniedAPIError,
)
from rest_framework.serializers import Serializer
from rest_framework.request import Request
from rest_framework.permissions import BasePermission
from rest_framework.generics import GenericAPIView
from typing import Dict, List, Any, Callable


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

    application_mapping: Dict[str, Any]
    authentication_mapping: Dict[str, Any]
    permission_mapping: Dict[str, Any]
    serializer_mapping: Dict[str, Any]

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if not GenericAPIView in cls.__bases__:
            raise TypeError(
                f"The {cls.__name__} class must inherit from GenericAPIView. Make sure your view definition includes GenericAPIView as a base class when using the MethodHTTPMapped class."
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
            return [auth() for auth in self.authentication_classes]

        return [auth() for auth in authentication_classes]

    def get_permissions(self) -> List[BasePermission]:
        """
        Returns the permission classes that the view should use for the incoming
        request based on the HTTP method.
        """

        try:
            permission_classes = self.permission_mapping[self.request.method]
        except (AttributeError, KeyError):
            return [permission() for permission in self.permission_classes]

        return [permission() for permission in permission_classes]

    def get_serializer_class(self) -> Serializer:
        """
        Returns the serializer class that the view should use for the incoming
        request based on the HTTP method.
        """

        try:
            return self.serializer_mapping[self.request.method]
        except (AttributeError, KeyError):
            return self.serializer_class

    def get_application_class(self, **dependencies: Any):
        """
        Returns the application class that the view should use for the incoming
        request based on the HTTP method.

        #### Parameters:
        - dependencies: Any dependencies that the application class requires.
        """

        try:
            application_class = self.application_mapping[self.request.method]

            return application_class(**dependencies)
        except (AttributeError, KeyError):
            return self.application_class


class PermissionMixin:
    """
    A class that provides permission checking functionality for views.

    This mixin class provides a method to check if the request should be permitted
    based on the permissions defined in the view.
    """

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if not GenericAPIView in cls.__bases__:
            raise TypeError(
                f"The {cls.__name__} class must inherit from GenericAPIView. Make sure your view definition includes GenericAPIView as a base class when using the PermissionMixin class."
            )

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
            raise NotAuthenticatedAPIError()
        raise PermissionDeniedAPIError(detail=message, code=code)

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
