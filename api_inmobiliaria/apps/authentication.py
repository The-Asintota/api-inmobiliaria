from apps.users.models import User
from apps.api_exceptions import AuthenticationFailedAPIError, JWTAPIError
from rest_framework_simplejwt.authentication import (
    JWTAuthentication as BaseAJWTuthentication,
)
from rest_framework_simplejwt.utils import get_md5_hash_password
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import Token


class JWTAuthentication(BaseAJWTuthentication):
    """
    JWTAuthentication is a class that handles JSON web token authentication.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        from apps.users.infrastructure.db import UserRepository

        self._user_repository = UserRepository

    def get_validated_token(self, raw_token: bytes) -> Token:
        """
        Validates an encoded JSON web token and returns a validated token wrapper
        object.
        """

        messages = []

        for AuthToken in api_settings.AUTH_TOKEN_CLASSES:
            try:
                return AuthToken(raw_token)
            except TokenError as e:
                messages.append(
                    {
                        "token_type": AuthToken.token_type,
                        "message": e.args[0],
                    }
                )

        raise JWTAPIError(detail=messages)

    def get_user(self, validated_token: Token) -> User:
        """
        Attempts to find and return a user using the given validated token.
        """

        try:
            user_uuid = validated_token[api_settings.USER_ID_CLAIM]
        except KeyError:
            raise JWTAPIError(
                detail="Token contained no recognizable user identification"
            )

        user = self._user_repository.get_user_data(uuid=user_uuid).first()

        if not user:
            raise AuthenticationFailedAPIError(
                code="authentication_failed", detail="User does not exist."
            )

        if not user.is_active:
            raise AuthenticationFailedAPIError(
                code="authentication_failed",
                detail="Cuenta del usuario inactiva.",
            )

        if api_settings.CHECK_REVOKE_TOKEN:
            if validated_token.get(
                api_settings.REVOKE_TOKEN_CLAIM
            ) != get_md5_hash_password(user.password):
                raise AuthenticationFailedAPIError(
                    code="authentication_failed",
                    detail="The user's password has been changed.",
                )

        return user
