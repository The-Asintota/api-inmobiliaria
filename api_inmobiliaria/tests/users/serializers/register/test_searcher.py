from apps.users.infrastructure.serializers import SearcherRegisterSerializer
from apps.users.domain.constants import SearcherProperties, UserProperties
from apps.users.models import User
from apps.utils import ERROR_MESSAGES
from tests.factory import UserFactory
from tests.utils import empty_queryset, fake
from unittest.mock import Mock, patch
from typing import Dict, List
import pytest


class TestRegisterSerializer:
    """
    This class encapsulates the tests for the serializer in charge of validating
    the data required for the registration of a user with the "Searcher" role.
    """

    serializer_class = SearcherRegisterSerializer
    user_factory = UserFactory

    @patch("apps.users.infrastructure.serializers.base.UserRepository")
    def test_valid_data(self, user_repository_mock: Mock) -> None:
        """
        This test is responsible for validating the expected behavior of the
        serializer when the log data is valid.
        """

        # Creating the user data to be used in the test
        data = {
            "name": "Nombre del usuario",
            "last_name": "Apellido del usuario",
            "email": "user1@email.com",
            "password": "contraseña1234",
            "confirm_password": "contraseña1234",
        }

        # Mocking the methods
        get_user_data: Mock = user_repository_mock.get_user_data
        get_user_data.return_value = empty_queryset(model=User)

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
                    "name": [ERROR_MESSAGES["required"]],
                    "last_name": [ERROR_MESSAGES["required"]],
                    "email": [ERROR_MESSAGES["required"]],
                    "password": [ERROR_MESSAGES["required"]],
                    "confirm_password": [ERROR_MESSAGES["required"]],
                },
            ),
            (
                {
                    "name": "User123",
                    "last_name": "User_@123",
                    "email": "useremail.com",
                    "password": "contraseña1234",
                    "confirm_password": "contraseña1234",
                },
                {
                    "email": [ERROR_MESSAGES["invalid"]],
                    "name": [ERROR_MESSAGES["invalid"]],
                    "last_name": [ERROR_MESSAGES["invalid"]],
                },
            ),
            (
                {
                    "name": fake.bothify(text=f"{'?' * 41}"),
                    "last_name": fake.bothify(text=f"{'?' * 41}"),
                    "email": f"user{fake.random_number(digits=41)}@email.com",
                    "password": fake.password(length=41, special_chars=True),
                },
                {
                    "name": [
                        ERROR_MESSAGES["max_length"].format(
                            max_length=SearcherProperties.NAME_MAX_LENGTH.value,
                        ),
                    ],
                    "last_name": [
                        ERROR_MESSAGES["max_length"].format(
                            max_length=SearcherProperties.LAST_NAME_MAX_LENGTH.value,
                        ),
                    ],
                    "email": [
                        ERROR_MESSAGES["max_length"].format(
                            max_length=UserProperties.EMAIL_MAX_LENGTH.value,
                        ),
                    ],
                    "password": [
                        ERROR_MESSAGES["max_length"].format(
                            max_length=UserProperties.PASSWORD_MAX_LENGTH.value,
                        ),
                    ],
                    "confirm_password": [ERROR_MESSAGES["required"]],
                },
            ),
            (
                {
                    "name": "Nombre del usuario",
                    "last_name": "Apellido del usuario",
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
                    "name": "Nombre del usuario",
                    "last_name": "Apellido del usuario",
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
    def test_invalid_data(
        self,
        user_repository_mock: Mock,
        data: Dict[str, str],
        error_messages: Dict[str, List],
    ) -> None:
        """
        This test is responsible for validating the expected behavior of the
        serializer when the record data is invalid and does not exist in the
        database.
        """

        # Mocking the method
        get_user_data: Mock = user_repository_mock.get_user_data
        get_user_data.return_value = empty_queryset(model=User)

        serializer = self.serializer_class(data=data)

        # Asserting the serializer is not valid and the data is correct
        assert not serializer.is_valid()
        assert serializer.validated_data == {}

        errors_formatted = {
            field: [str(error) for error in errors]
            for field, errors in serializer.errors.items()
        }

        for field, message in error_messages.items():
            assert errors_formatted[field] == message

    @pytest.mark.parametrize(
        argnames="data, error_messages",
        argvalues=[
            (
                {
                    "name": "Nombre del usuario",
                    "last_name": "Apellido del usuario",
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
        user_repository_mock: Mock,
        queryset: Mock,
        data: Dict[str, str],
        error_messages: Dict[str, List],
    ) -> None:
        """
        This test is responsible for validating the expected behavior of the
        serializer when the record data already exists in the database.
        """

        # Mocking the methods
        get_user_data: Mock = user_repository_mock.get_user_data
        user: Mock = queryset.first
        get_user_data.return_value = queryset
        user.return_value = User

        serializer = self.serializer_class(data=data)

        # Asserting the serializer is not valid and the data is correct
        assert not serializer.is_valid()
        assert serializer.validated_data == {}

        errors_formatted = {
            field: [str(error) for error in errors]
            for field, errors in serializer.errors.items()
        }

        for field, message in error_messages.items():
            assert errors_formatted[field] == message
