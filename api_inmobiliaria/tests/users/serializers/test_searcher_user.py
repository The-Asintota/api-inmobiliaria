from apps.users.infrastructure.serializers import (
    SearcherUserRegisterSerializer,
)
from apps.users.domain.constants import SearcherUser
from apps.users.models import User
from apps.utils import ERROR_MESSAGES
from tests.utils import empty_queryset
from unittest.mock import Mock, patch
from typing import Dict, Any
from faker import Faker
import pytest


fake = Faker("es_CO")


class TestSerializer:
    """
    A class to test the `SearcherUserRegisterSerializer` class.
    """

    serializer_class = SearcherUserRegisterSerializer

    @patch("apps.users.infrastructure.serializers.base.UserRepository")
    def test_correct_execution(self, repository: Mock) -> None:
        data = {
            "full_name": "Nombre Apellido",
            "email": "user1@email.com",
            "password": "contraseña1234",
            "confirm_password": "contraseña1234",
        }

        # Mocking the methods
        get: Mock = repository.get

        # Setting the return values
        get.return_value = empty_queryset(model=User)

        # Instantiating the serializer
        serializer = self.serializer_class(data=data)

        # Asserting the serializer is valid and the data is correct
        assert serializer.is_valid()

        for field, value in data.items():
            assert serializer.validated_data[field] == value

    @pytest.mark.parametrize(
        argnames="data, error_messages",
        argvalues=[
            (
                {},
                {
                    "full_name": [ERROR_MESSAGES["required"]],
                    "email": [ERROR_MESSAGES["required"]],
                    "password": [ERROR_MESSAGES["required"]],
                    "confirm_password": [ERROR_MESSAGES["required"]],
                },
            ),
            (
                {
                    "full_name": "User123",
                    "email": "useremail.com",
                    "password": "contraseña1234",
                    "confirm_password": "contraseña1234",
                },
                {
                    "email": [ERROR_MESSAGES["invalid"]],
                    "full_name": [ERROR_MESSAGES["invalid"]],
                },
            ),
            (
                {
                    "full_name": fake.bothify(text=f"{'?' * 41}"),
                    "email": f"user{fake.random_number(digits=41)}@email.com",
                    "password": fake.password(length=21, special_chars=True),
                },
                {
                    "full_name": [
                        ERROR_MESSAGES["max_length"].format(
                            max_length=SearcherUser.FULL_NAME_MAX_LENGTH.value,
                        ),
                    ],
                    "email": [
                        ERROR_MESSAGES["max_length"].format(
                            max_length=SearcherUser.EMAIL_MAX_LENGTH.value,
                        ),
                    ],
                    "password": [
                        ERROR_MESSAGES["max_length"].format(
                            max_length=SearcherUser.PASSWORD_MAX_LENGTH.value,
                        ),
                    ],
                    "confirm_password": [ERROR_MESSAGES["required"]],
                },
            ),
            (
                {
                    "full_name": "Nombre Apellido",
                    "email": "user1@email.com",
                    "password": "contraseña1234",
                    "confirm_password": "contraseña5678",
                },
                {
                    "confirm_password": [ERROR_MESSAGES["password_mismatch"]],
                },
            ),
            (
                {
                    "full_name": "Nombre Apellido",
                    "email": "user1@email.com",
                    "password": f"{fake.random_number(digits=10)}",
                },
                {
                    "password": [ERROR_MESSAGES["password_no_upper_lower"]],
                    "confirm_password": [ERROR_MESSAGES["required"]],
                },
            ),
        ],
        ids=[
            "empty_data",
            "invalid_data",
            "max_length_data",
            "passwords_not_match",
            "password_no_upper_lower",
        ],
    )
    @patch("apps.users.infrastructure.serializers.base.UserRepository")
    def test_failed_execution(
        self,
        repository: Mock,
        data: Dict[str, Dict],
        error_messages: Dict[str, Any],
    ) -> None:
        # Mocking the methods
        get: Mock = repository.get

        # Setting the return values
        get.return_value = empty_queryset(model=User)

        # Instantiating the serializer
        serializer = self.serializer_class(data=data)

        # Asserting the serializer is not valid and the data is correct
        assert not serializer.is_valid()
        assert serializer.validated_data == {}

        errors = serializer.errors.copy()
        errors_formatted = {
            field: [str(error) for error in errors]
            for field, errors in errors.items()
        }

        for field, message in error_messages.items():
            assert errors_formatted[field] == message

    @pytest.mark.parametrize(
        argnames="data, error_messages",
        argvalues=[
            (
                {
                    "full_name": "Nombre Apellido",
                    "email": "user1@email.com",
                    "password": "contraseña1234",
                    "confirm_password": "contraseña1234",
                },
                {
                    "email": [ERROR_MESSAGES["email_in_use"]],
                },
            ),
        ],
        ids=["email_in_use"],
    )
    @patch("apps.users.infrastructure.serializers.base.UserRepository")
    def test_data_used(
        self,
        repository: Mock,
        queryset: Mock,
        data: Dict[str, Dict],
        error_messages: Dict[str, Any],
    ) -> None:
        # Mocking the methods
        get: Mock = repository.get
        user: Mock = queryset.first

        # Setting the return values
        get.return_value = queryset
        user.return_value = User

        # Instantiating the serializer
        serializer = self.serializer_class(data=data)

        # Asserting the serializer is not valid and the data is correct
        assert not serializer.is_valid()
        assert serializer.validated_data == {}

        errors = serializer.errors.copy()
        errors_formatted = {
            field: [str(error) for error in errors]
            for field, errors in errors.items()
        }

        for field, message in error_messages.items():
            assert errors_formatted[field] == message
