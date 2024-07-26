from apps.users.infrastructure.db import UserRepository
from apps.users.domain.constants import UserProperties
from apps.utils import ErrorMessagesSerializer, ERROR_MESSAGES
from rest_framework import serializers
from django.core.validators import RegexValidator
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from typing import Dict


class BaseUserDataSerializer(ErrorMessagesSerializer):
    """
    Defines the base data of a user.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__user_repository = UserRepository

    email = serializers.CharField(
        required=True,
        max_length=UserProperties.EMAIL_MAX_LENGTH.value,
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
        max_length=UserProperties.PASSWORD_MAX_LENGTH.value,
        min_length=UserProperties.PASSWORD_MIN_LENGTH.value,
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
    confirm_password = serializers.CharField(
        required=True, write_only=True, style={"input_type": "password"}
    )

    def validate_email(self, value: str) -> str:
        """
        Validate that the email is not in use.
        """

        user = self.__user_repository.get_user_data(email=value)

        if user.first():
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

    def validate(self, data: Dict[str, str]) -> Dict[str, str]:
        """
        Check if the password and confirm password match.
        """

        password = data["password"]
        confirm_password = data["confirm_password"]

        if not password == confirm_password:
            raise serializers.ValidationError(
                code="invalid_data",
                detail={
                    "confirm_password": [
                        ERROR_MESSAGES["password_mismatch"],
                    ]
                },
            )

        return data
