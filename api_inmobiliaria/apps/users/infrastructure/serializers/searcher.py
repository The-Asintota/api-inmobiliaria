from apps.users.infrastructure.db import UserRepository
from apps.users.infrastructure.serializers.base import BaseUserDataSerializer
from apps.users.infrastructure.schemas.searcher import (
    SearcherRegisterSerializerSchema,
)
from apps.users.domain.constants import UserRoles, SearcherProperties
from apps.users.models import User, Searcher
from apps.utils.messages import ErrorMessagesSerializer, ERROR_MESSAGES
from rest_framework import serializers
from django.core.validators import RegexValidator
from phonenumber_field.serializerfields import PhoneNumberField
from typing import Dict, Any


class RoleDataSerializer(ErrorMessagesSerializer):
    """
    Defines the fields that are required for the searcher user profile.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.__user_repository = UserRepository

    name = serializers.CharField(
        required=False,
        max_length=SearcherProperties.NAME_MAX_LENGTH.value,
        error_messages={
            "max_length": ERROR_MESSAGES["max_length"].format(
                max_length="{max_length}"
            ),
        },
        validators=[
            RegexValidator(
                regex=r"^[A-Za-zñÑ\s]+$",
                code="invalid_data",
                message=ERROR_MESSAGES["invalid"],
            ),
        ],
    )
    last_name = serializers.CharField(
        required=False,
        max_length=SearcherProperties.LAST_NAME_MAX_LENGTH.value,
        error_messages={
            "max_length": ERROR_MESSAGES["max_length"].format(
                max_length="{max_length}"
            ),
        },
        validators=[
            RegexValidator(
                regex=r"^[A-Za-zñÑ\s]+$",
                code="invalid_data",
                message=ERROR_MESSAGES["invalid"],
            ),
        ],
    )
    cc = serializers.CharField(
        required=False,
        min_length=SearcherProperties.CC_MIN_LENGTH.value,
        max_length=SearcherProperties.CC_MAX_LENGTH.value,
        error_messages={
            "min_length": ERROR_MESSAGES["min_length"].format(
                min_length=SearcherProperties.CC_MIN_LENGTH.value
            ),
            "max_length": ERROR_MESSAGES["max_length"].format(
                max_length=SearcherProperties.CC_MAX_LENGTH.value
            ),
        },
        validators=[
            RegexValidator(
                regex=r"^\d+$",
                code="invalid_data",
                message=ERROR_MESSAGES["invalid"],
            ),
        ],
    )
    address = serializers.CharField(
        required=False,
        max_length=SearcherProperties.ADDRESS_MAX_LENGTH.value,
        error_messages={
            "max_length": ERROR_MESSAGES["max_length"].format(
                max_length="{max_length}"
            ),
        },
    )
    phone_number = PhoneNumberField(
        required=False,
        max_length=SearcherProperties.PHONE_NUMBER_MAX_LENGTH.value,
        error_messages={
            "max_length": ERROR_MESSAGES["max_length"].format(
                max_length="{max_length}"
            ),
        },
    )

    def validate_address(self, value: str) -> str:
        """
        Validate that the address is not in use.
        """

        searcher = self.__user_repository.get_role_data(
            role=UserRoles.SEARCHER.value,
            address=value,
        )

        if searcher.first():
            raise serializers.ValidationError(
                code="invalid_data",
                detail=ERROR_MESSAGES["address_in_use"],
            )

        return value

    def validate_phone_number(self, value: str) -> str:
        """
        Validate that the phone number is not in use.
        """

        searcher = self.__user_repository.get_role_data(
            role=UserRoles.SEARCHER.value,
            phone_number=value,
        )

        if searcher.first():
            raise serializers.ValidationError(
                code="invalid_data",
                detail=ERROR_MESSAGES["phone_in_use"],
            )

        return value


@SearcherRegisterSerializerSchema
class SearcherRegisterUserSerializer(BaseUserDataSerializer):
    """
    Defines the fields that are required for the searcher user registration.
    """

    name = serializers.CharField(
        required=True,
        max_length=SearcherProperties.NAME_MAX_LENGTH.value,
        error_messages={
            "max_length": ERROR_MESSAGES["max_length"].format(
                max_length="{max_length}"
            ),
        },
        validators=[
            RegexValidator(
                regex=r"^[A-Za-zñÑ\s]+$",
                code="invalid_data",
                message=ERROR_MESSAGES["invalid"],
            ),
        ],
    )
    last_name = serializers.CharField(
        required=True,
        max_length=SearcherProperties.LAST_NAME_MAX_LENGTH.value,
        error_messages={
            "max_length": ERROR_MESSAGES["max_length"].format(
                max_length="{max_length}"
            ),
        },
        validators=[
            RegexValidator(
                regex=r"^[A-Za-zñÑ\s]+$",
                code="invalid_data",
                message=ERROR_MESSAGES["invalid"],
            ),
        ],
    )
    confirm_password = serializers.CharField(
        required=True, write_only=True, style={"input_type": "password"}
    )

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


class SearcherUserReadOnlySerializer(serializers.Serializer):
    """
    Defines the fields of the searcher user information for reading.
    """

    def __init__(self, role_instance: Searcher, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.role_instance = role_instance

    def to_representation(self, instance: User) -> Dict[str, Any]:

        return {
            "base_data": {"email": instance.email},
            "role_data": {
                "name": self.role_instance.name,
                "last_name": self.role_instance.last_name,
                "cc": self.role_instance.cc,
                "address": self.role_instance.address,
                "phone_number": self.role_instance.phone_number,
                "is_phone_verified": self.role_instance.is_phone_verified,
            },
        }
