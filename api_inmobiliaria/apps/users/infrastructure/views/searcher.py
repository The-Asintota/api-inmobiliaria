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
from apps.permissions import IsJWTOwner
from authentication.jwt import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import Serializer
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.generics import GenericAPIView
from rest_framework import status


class RegisterSearcherAPIView(GenericAPIView):
    """
    API view for managing operations for users with `searcher role`.

    It uses a mapping approach to determine the appropriate application logic,
    permissions, and serializers based on the HTTP method of the incoming request.
    """

    authentication_classes = []
    permission_classes = []
    application_class = RegisterUser
    serializer_class = SearcherRegisterUserSerializer

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

        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():
            return Response(
                data={
                    "code": "invalid_request_data",
                    "detail": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
                content_type="application/json",
            )

        register = self.application_class(user_repository=UserRepository)
        register.searcher(data=serializer.validated_data, request=request)

        return Response(status=status.HTTP_201_CREATED)


class SearcherAPIView(MethodHTTPMapped, PermissionMixin, GenericAPIView):
    """
    API view for managing operations for users with `searcher role`.

    It uses a mapping approach to determine the appropriate application logic,
    permissions, and serializers based on the HTTP method of the incoming request.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsJWTOwner]
    application_mapping = {"GET": UserDataManager}
    serializer_mapping = {
        "GET": SearcherUserReadOnlySerializer,
    }

    @GETSearcherSchema
    def get(self, request: Request, *args, **kwargs) -> Response:
        """
        Handle GET requests to obtain user information.

        This method allows the user account information to be returned based on the
        'user_uuid' indicated in the request path, without revealing sensitive
        information.
        """

        app: UserDataManager = self.get_application_class(
            user_repository=UserRepository
        )
        role_user = app.get(user=request.user)

        serializer_class = self.get_serializer_class()
        serializer: Serializer = serializer_class(
            instance=request.user, role_instance=role_user
        )

        return Response(
            data=serializer.data,
            status=status.HTTP_200_OK,
            content_type="application/json",
        )
