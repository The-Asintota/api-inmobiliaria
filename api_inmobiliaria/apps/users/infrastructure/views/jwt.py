from apps.users.infrastructure.schemas.jwt import (
    AuthenticationSchema,
    UpdateTokensSchema,
    LogoutSchema,
)
from apps.users.infrastructure.serializers import (
    AuthenticationSerializer,
    TokenObtainPairSerializer,
    UpdateTokenSerializer,
    LogoutSerializer,
)
from apps.users.infrastructure.db import JWTRepository, UserRepository
from apps.users.applications import JWTUsesCases
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status, generics
from typing import Dict, Any, List


class AuthenticationAPIView(TokenObtainPairView):
    """
    API View for user authentication.

    This view handles the `POST` request to authenticate a user in the real estate
    management system.
    """

    authentication_classes = []
    permission_classes = []
    serializer_class = AuthenticationSerializer
    application_class = JWTUsesCases

    def _handle_valid_request(self, data: Dict[str, Any]) -> Response:
        tokens = self.application_class(
            jwt_class=TokenObtainPairSerializer,
        ).authenticate_user(credentials=data)

        return Response(
            data=tokens,
            status=status.HTTP_200_OK,
            content_type="application/json",
        )

    @staticmethod
    def _handle_invalid_request(errors: List[Dict[str, List]]) -> Response:

        return Response(
            data={
                "code": "invalid_request_data",
                "detail": errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
            content_type="application/json",
        )

    @AuthenticationSchema
    def post(self, request: Request, *args, **kwargs) -> Response:
        """
        Handle POST requests for user authentication.

        This method allows for the authentication of a user, it expects a POST request
        with their credentials. Successful authentication will result in the creation
        of the user's JSON Web Tokens if their credentials are valid, their account is
        active, and they have the necessary permissions to perform this action.
        """

        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            return self._handle_valid_request(data=serializer.validated_data)

        return self._handle_invalid_request(errors=serializer.errors)


class UpdateTokenAPIView(generics.GenericAPIView):
    """
    API View for refreshing user tokens. This view handles the request to
    refresh a user's access and refresh tokens in the system.
    """

    authentication_classes = []
    permission_classes = []
    serializer_class = UpdateTokenSerializer
    application_class = JWTUsesCases

    def _handle_valid_request(self, data: Dict[str, Any]) -> Response:
        tokens = self.application_class(
            jwt_class=TokenObtainPairSerializer,
            jwt_repository=JWTRepository,
            user_repository=UserRepository,
        ).update_tokens(data=data)

        return Response(
            data=tokens,
            status=status.HTTP_200_OK,
            content_type="application/json",
        )

    @staticmethod
    def _handle_invalid_request(errors: List[Dict[str, List]]) -> Response:

        return Response(
            data={
                "code": "invalid_request_data",
                "detail": errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
            content_type="application/json",
        )

    @UpdateTokensSchema
    def post(self, request: Request, *args, **kwargs) -> Response:
        """
        Handle POST requests for token refresh.

        This method allows updating the JSON Web Tokens of an authenticated user,
        waiting for a POST request with the access and update tokens. A successful
        refresh will consist of creating new tokens to keep the user authenticated and
        invalidating the previous refresh token by adding it to the blacklist.
        """

        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            return self._handle_valid_request(data=serializer.validated_data)

        return self._handle_invalid_request(errors=serializer.errors)


class LogoutAPIView(generics.GenericAPIView):
    """
    API View for user logout. This view handles the request to logout a user
    from the system.
    """

    authentication_classes = []
    permission_classes = []
    serializer_class = LogoutSerializer
    application_class = JWTUsesCases

    def _handle_valid_request(self, data: Dict[str, Any]) -> Response:
        self.application_class(
            jwt_repository=JWTRepository,
            user_repository=UserRepository,
        ).logout_user(data=data)

        return Response(
            status=status.HTTP_200_OK,
            content_type="application/json",
        )

    @staticmethod
    def _handle_invalid_request(errors: List[Dict[str, List]]) -> Response:

        return Response(
            data={
                "code": "invalid_request_data",
                "detail": errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
            content_type="application/json",
        )

    @LogoutSchema
    def post(self, request: Request, *args, **kwargs) -> Response:
        """
        Handle POST requests for user logout.

        This method allows you to log out a user. Wait for a POST request with the
        access and update JSON Web Tokens. A successful logout will consist of
        invalidating the tokens by adding them to the blacklist if they have not yet
        expired.
        """

        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            return self._handle_valid_request(data=serializer.validated_data)

        return self._handle_invalid_request(errors=serializer.errors)
