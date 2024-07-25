from apps.users.infrastructure.db import UserRepository
from apps.users.infrastructure.serializers.base import BaseUserSerializer
from apps.users.infrastructure.schemas.searcher_user import (
    SearcherUserRegisterSerializerSchema,
)
from apps.users.domain.constants import SearcherUser
from apps.users.models import UserRoles
from apps.utils import ErrorMessagesSerializer
from apps.constants import ERROR_MESSAGES
from rest_framework import serializers
from django.core.validators import RegexValidator
from phonenumber_field.serializerfields import PhoneNumberField


class SearcherUserProfileDataSerializer(ErrorMessagesSerializer):
    """
    Defines the fields that are required for the searcher user profile.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._user_repository = UserRepository
        self.profile_queryset = None

    full_name = serializers.CharField(
        required=True,
        max_length=SearcherUser.FULL_NAME_MAX_LENGTH.value,
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
    address = serializers.CharField(
        required=True,
        max_length=SearcherUser.ADDRESS_MAX_LENGTH.value,
        error_messages={
            "max_length": ERROR_MESSAGES["max_length"].format(
                max_length="{max_length}"
            ),
        },
    )
    phone_number = PhoneNumberField(
        required=True,
        max_length=SearcherUser.PHONE_NUMBER_MAX_LENGTH.value,
        error_messages={
            "max_length": ERROR_MESSAGES["max_length"].format(
                max_length="{max_length}"
            ),
        },
    )

    def validate_full_name(self, value: str) -> str:
        if not self.profile_queryset:
            self.profile_queryset = self._user_repository.get_role_data(
                role=UserRoles.SEARCHER.value, full_name=value
            )
        elif self.profile_queryset.first():
            raise serializers.ValidationError(
                code="invalid_data",
                detail=ERROR_MESSAGES["name_in_use"],
            )

        return value

    def validate_address(self, value: str) -> str:
        if not self.profile_queryset:
            self.profile_queryset = self._user_repository.get_role_data(
                role=UserRoles.SEARCHER.value,
                address=value,
            )
        elif self.profile_queryset.first():
            raise serializers.ValidationError(
                code="invalid_data",
                detail=ERROR_MESSAGES["address_in_use"],
            )

        return value

    def validate_phone_number(self, value: str) -> str:
        if not self.profile_queryset:
            self.profile_queryset = self._user_repository.get_role_data(
                role=UserRoles.SEARCHER.value,
                phone_number=value,
            )
        elif self.profile_queryset.first():
            raise serializers.ValidationError(
                code="invalid_data",
                detail=ERROR_MESSAGES["phone_in_use"],
            )

        return value


class SearcherUserSerializer(ErrorMessagesSerializer):
    """
    Defines the fields that are required for the searcher user.
    """

    base_data = BaseUserSerializer()
    profile_data = SearcherUserProfileDataSerializer()


@SearcherUserRegisterSerializerSchema
class SearcherUserRegisterSerializer(BaseUserSerializer):
    """
    Defines the fields that are required for the searcher user registration.
    """

    full_name = serializers.CharField(
        required=True,
        max_length=SearcherUser.FULL_NAME_MAX_LENGTH.value,
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
