from apps.users.infrastructure.repositories import UserRepository
from apps.users.constants import BaseUserProperties
from utils.messages import ErrorMessagesSerializer, ERROR_MESSAGES
from rest_framework import serializers
from django.core.validators import RegexValidator
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


# Base user properties
EMAIL_MAX_LENGTH = BaseUserProperties.EMAIL_MAX_LENGTH.value
PASSWORD_MAX_LENGTH = BaseUserProperties.PASSWORD_MAX_LENGTH.value
PASSWORD_MIN_LENGTH = BaseUserProperties.PASSWORD_MIN_LENGTH.value


class BaseUserSerializer(ErrorMessagesSerializer, serializers.Serializer):
    """
    Defines the base data of a user.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._user_repository = UserRepository

    email = serializers.CharField(
        required=True,
        max_length=EMAIL_MAX_LENGTH,
        error_messages={
            "max_length": ERROR_MESSAGES["max_length"].format(
                max_length="{max_length}"
            ),
        },
        validators=[
            RegexValidator(
                regex=r"^([A-Za-z0-9]+[-_.])*[A-Za-z0-9]+@[A-Za-z]+(\.[A-Z|a-z]{2,4}){1,2}$",
                code="invalid_data",
                message=ERROR_MESSAGES["invalid"],
            ),
        ],
    )
    password = serializers.CharField(
        required=True,
        write_only=True,
        max_length=PASSWORD_MAX_LENGTH,
        min_length=PASSWORD_MIN_LENGTH,
        style={"input_type": "password"},
        error_messages={
            "max_length": ERROR_MESSAGES["max_length"].format(
                max_length="{max_length}"
            ),
            "min_length": ERROR_MESSAGES["min_length"].format(
                min_length="{min_length}"
            ),
        },
    )

    def validate_email(self, value: str) -> str:
        """
        Validate that the email is not in use.
        """

        exists = self._user_repository.base_data_exists(email=value)

        if exists:
            raise serializers.ValidationError(
                code="invalid_data",
                detail=ERROR_MESSAGES["email_in_use"],
            )

        return value

    def validate_password(self, value: str) -> str:
        """
        Validate that the password is not a common password and has at least one
        uppercase and one lowercase letter.
        """

        try:
            validate_password(value)
        except ValidationError:
            if value.isdecimal():
                raise serializers.ValidationError(
                    code="invalid_data",
                    detail=ERROR_MESSAGES["password_no_upper_lower"],
                )
            raise serializers.ValidationError(
                code="invalid_data",
                detail=ERROR_MESSAGES["password_common"],
            )

        return value


class BaseUserReadOnlySerializer(serializers.Serializer):
    """
    Defines the base data of a user for read only.
    """

    email = serializers.EmailField(read_only=True)
