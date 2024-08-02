from apps.users.infrastructure.schemas.jwt import (
    AuthenticationSerializerSchema,
    UpdateTokenSerializerSchema,
    LogoutSerializerSchema,
)
from apps.users.infrastructure.db import JWTRepository
from apps.users.domain.typing import AccessToken, RefreshToken
from apps.users.domain.constants import UserProperties
from apps.users.models import User
from apps.utils import ErrorMessagesSerializer, decode_jwt, ERROR_MESSAGES
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer as BaseTokenSerializer,
)
from rest_framework_simplejwt.tokens import RefreshToken as TokenClass
from rest_framework import serializers
from jwt import DecodeError, ExpiredSignatureError
from typing import Dict, Any, Tuple


@AuthenticationSerializerSchema
class AuthenticationSerializer(ErrorMessagesSerializer):
    """
    Handles the data for user authentication. Checks that the provided email and
    password meet the necessary requirements.
    """

    email = serializers.CharField(
        required=True,
        max_length=UserProperties.EMAIL_MAX_LENGTH.value,
        error_messages={
            "max_length": ERROR_MESSAGES["max_length"].format(
                max_length="{max_length}"
            ),
        },
    )
    password = serializers.CharField(
        required=True,
        max_length=UserProperties.PASSWORD_MAX_LENGTH.value,
        error_messages={
            "max_length": ERROR_MESSAGES["max_length"].format(
                max_length="{max_length}"
            ),
        },
    )


class TokenObtainPairSerializer(BaseTokenSerializer):
    """
    Defines the custom serializer used to generate the access and refresh tokens wit
    custom payload.
    """

    jwt_repository = JWTRepository

    @classmethod
    def get_token(cls, user: User) -> Tuple[AccessToken, RefreshToken]:
        """
        Generates the JSON WEB Tokens for the user and saves them to the database.
        """

        token: TokenClass = cls.token_class.for_user(user=user)
        token["role"] = user.content_type.model_class().__name__.lower()
        refresh = token
        access = token.access_token

        for token in [refresh, access]:
            cls.jwt_repository.add_to_checklist(
                token=token,
                payload=token.payload,
                user=user,
            )

        return access.__str__(), refresh.__str__()


class BaseUpdateLogoutSerializer(serializers.Serializer):
    """
    Base class for the serializers that update or logout a user.
    """

    refresh = serializers.CharField(required=True)
    access = serializers.CharField(required=True)

    def validate_refresh(self, value: str) -> Dict[str, Any]:
        try:
            self._refresh_payload = decode_jwt(token=value)
        except ExpiredSignatureError:
            raise serializers.ValidationError(
                detail="Token is expired.", code="token_error"
            )
        except DecodeError:
            raise serializers.ValidationError(
                detail="Token is invalid.", code="token_error"
            )

        return self._refresh_payload

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check that the refresh and access tokens belong to the same user.
        """

        if (
            self._refresh_payload["user_uuid"]
            != self._access_payload["user_uuid"]
        ):
            raise serializers.ValidationError(
                code="token_error",
                detail={"access": ["Tokens do not match the same user."]},
            )

        return attrs


@UpdateTokenSerializerSchema
class UpdateTokenSerializer(BaseUpdateLogoutSerializer):
    """
    Handles data to refresh tokens of a user.
    """

    def validate_access(self, value: str) -> Dict[str, Any]:
        try:
            decode_jwt(token=value)
        except ExpiredSignatureError:
            self._access_payload = decode_jwt(
                token=value, options={"verify_exp": False}
            )

            return self._access_payload
        except DecodeError:
            raise serializers.ValidationError(
                detail="Token is invalid.", code="token_error"
            )

        raise serializers.ValidationError(
            detail="Token is not expired.", code="token_error"
        )


@LogoutSerializerSchema
class LogoutSerializer(BaseUpdateLogoutSerializer):
    """
    Handles data to logout user.

    """

    def validate_access(self, value: str) -> Dict[str, Any]:
        try:
            self._access_payload = decode_jwt(
                token=value, options={"verify_exp": False}
            )
        except DecodeError:
            raise serializers.ValidationError(
                detail="Token is invalid.", code="token_error"
            )

        return self._access_payload
