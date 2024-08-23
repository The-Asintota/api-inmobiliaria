from apps.users.infrastructure.db import UserRepository
from apps.users.infrastructure.serializers import (
    SearcherRegisterUserSerializer,
    SearcherUserReadOnlySerializer,
)
from apps.users.infrastructure.schemas.searcher import (
    POSTSearcherSchema,
    GETSearcherSchema,
)
from apps.users.applications import RegisterUser, UserDataManager
from apps.utils.views import MethodHTTPMapped, PermissionMixin
from authentication.jwt import JWTAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.serializers import Serializer
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.generics import GenericAPIView
from rest_framework import status


class SearcherAPIView(MethodHTTPMapped, PermissionMixin, GenericAPIView):
    """
    API view for managing operations for users with `searcher role`.

    It uses a mapping approach to determine the appropriate application logic,
    permissions, and serializers based on the HTTP method of the incoming request.
    """

    authentication_mapping = {"POST": [], "GET": [JWTAuthentication]}
    permission_mapping = {"POST": [AllowAny], "GET": [IsAuthenticated]}
    application_mapping = {"POST": RegisterUser, "GET": UserDataManager}
    serializer_mapping = {
        "POST": SearcherRegisterUserSerializer,
        "GET": SearcherUserReadOnlySerializer,
    }

    @GETSearcherSchema
    def get(self, request: Request, *args, **kwargs) -> Response:
        """
        Handle GET requests to obtain user information.

        This method returns the user account information associated with the request's
        access token, without revealing sensitive data, provided the user has
        permission to read their own information.
        """

        searcher: UserDataManager = self.get_application_class(
            user_repository=UserRepository
        )
        role_user = searcher.get(user_base=request.user)

        serializer_class = self.get_serializer_class()
        serializer: Serializer = serializer_class(
            instance=request.user, role_instance=role_user
        )

        return Response(
            data=serializer.data,
            status=status.HTTP_200_OK,
            content_type="application/json",
        )

    @POSTSearcherSchema
    def post(self, request: Request, *args, **kwargs) -> Response:
        """
        Handle POST requests for searcher user registration.

        This method allows the registration of a new seacher user, waiting for a
        POST request with the registration data. A successful registration will
        consist of saving the user's information in the database and sending a
        message to the user's email with a link that will allow them to activate
        their account.
        """

        serializer_class = self.get_serializer_class()
        serializer: Serializer = serializer_class(data=request.data)

        if not serializer.is_valid():
            return Response(
                data={
                    "code": "invalid_request_data",
                    "detail": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
                content_type="application/json",
            )

        register: RegisterUser = self.get_application_class(
            user_repository=UserRepository
        )
        register.searcher(data=serializer.validated_data, request=request)

        return Response(status=status.HTTP_201_CREATED)
