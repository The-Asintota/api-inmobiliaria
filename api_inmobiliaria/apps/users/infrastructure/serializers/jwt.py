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
from apps.api_exceptions import JWTAPIError
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer as BaseTokenSerializer,
)
from rest_framework_simplejwt.tokens import RefreshToken as TokenClass
from rest_framework import serializers
from jwt import DecodeError, ExpiredSignatureError
from typing import Dict, Any, Tuple
from enum import Enum


class JWTErrorMessages(Enum):
    """
    Enum class for error messages related to serializers for JWTs.
    """

    REFRESH_INVALID = "Refresh token invalid."
    REFRESH_EXPIRED = "Refresh token has expired."
    ACCESS_INVALID = "Access token invalid."
    ACCESS_EXPIRED = "Access token has expired."
    ACCESS_NOT_EXPIRED = "Access token is not expired."
    USER_NOT_MATCH = "The user of the access token does not match the user of the refresh token."


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

    _jwt_repository = JWTRepository

    @classmethod
    def get_token(cls, user: User) -> Tuple[AccessToken, RefreshToken]:
        """
        Generates the JWT for the user and saves them to the database.
        """

        token: TokenClass = cls.token_class.for_user(user=user)
        token["role"] = user.content_type.model_class().__name__.lower()
        refresh = token
        access = token.access_token

        for token in [refresh, access]:
            cls._jwt_repository.add_to_checklist(
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

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.access_payload = None
        self.refresh_payload = None

    def validate_refresh(self, value: str) -> Dict[str, Dict[str, Any]]:
        """
        Check that the refresh token is valid and not expired.
        """

        try:
            if not self.refresh_payload:
                self.refresh_payload = decode_jwt(token=value)
        except ExpiredSignatureError:
            raise serializers.ValidationError(
                code=JWTAPIError.default_code,
                detail=JWTErrorMessages.REFRESH_EXPIRED.value,
            )
        except DecodeError:
            raise serializers.ValidationError(
                code=JWTAPIError.default_code,
                detail=JWTErrorMessages.REFRESH_INVALID.value,
            )

        return self.refresh_payload

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check that the refresh and access tokens belong to the same user.
        """

        if not self.access_payload:
            self.access_payload = decode_jwt(token=attrs["access"])
        elif not self.refresh_payload:
            self.refresh_payload = decode_jwt(token=attrs["refresh"])
        elif (
            self.refresh_payload["user_uuid"]
            != self.access_payload["user_uuid"]
        ):
            raise serializers.ValidationError(
                code=JWTAPIError.default_code,
                detail={
                    "access": [
                        JWTErrorMessages.USER_NOT_MATCH.value,
                    ]
                },
            )

        return attrs


@UpdateTokenSerializerSchema
class UpdateTokenSerializer(BaseUpdateLogoutSerializer):
    """
    Handles data to refresh tokens of a user.
    """

    def validate_access(self, value: str) -> Dict[str, Dict[str, Any]]:
        """
        Check that the access token is valid and not expired.
        """

        try:
            decode_jwt(token=value)
        except ExpiredSignatureError:
            if not self.access_payload:
                self.access_payload = decode_jwt(
                    token=value, options={"verify_exp": False}
                )

            return self.access_payload
        except DecodeError:
            raise serializers.ValidationError(
                code=JWTAPIError.default_code,
                detail=JWTErrorMessages.ACCESS_INVALID.value,
            )

        raise serializers.ValidationError(
            code=JWTAPIError.default_code,
            detail=JWTErrorMessages.ACCESS_NOT_EXPIRED.value,
        )


@LogoutSerializerSchema
class LogoutSerializer(BaseUpdateLogoutSerializer):
    """
    Handles data to logout user.
    """

    def validate_access(self, value: str) -> Dict[str, Dict[str, Any]]:
        """
        Check that the access token is valid.
        """

        try:
            if not self.access_payload:
                self.access_payload = decode_jwt(token=value)
        except ExpiredSignatureError:
            raise serializers.ValidationError(
                code=JWTAPIError.default_code,
                detail=JWTErrorMessages.ACCESS_EXPIRED.value,
            )
        except DecodeError:
            raise serializers.ValidationError(
                code=JWTAPIError.default_code,
                detail=JWTErrorMessages.ACCESS_INVALID.value,
            )

        return self.access_payload
