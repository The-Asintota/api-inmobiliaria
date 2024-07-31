from apps.users.domain.constants import (
    SearcherProperties,
    UserProperties,
    UserRoles,
)
from apps.users.models import User
from apps.exceptions import DatabaseConnectionError
from apps.utils import ERROR_MESSAGES
from tests.utils import fake
from django.test import Client
from django.urls import reverse
from unittest.mock import Mock, patch
from typing import Callable, Tuple, Dict
import pytest


@pytest.fixture
def setUp() -> Tuple[Client, str]:

    return Client(), reverse(viewname="searcher_user")


class TestAPIViewPOSTMethod:
    """
    This class encapsulates the tests for the view responsible for creating a
    user with the "Searcher" role.
    """

    @pytest.mark.django_db
    def test_request_valid(
        self, setUp: Tuple[Client, str], setup_database: Callable
    ) -> None:
        """
        This test is responsible for validating the expected behavior of the
        view when the request data is valid.
        """

        data = {
            "name": "Nombre del usuario",
            "last_name": "Apellido del usuario",
            "email": "user1@email.com",
            "password": "contraseña1234",
            "confirm_password": "contraseña1234",
        }

        # Simulating the request
        client, path = setUp
        response = client.post(
            path=path, data=data, content_type="application/json"
        )

        # Asserting that response data is correct
        assert response.status_code == 201

    @pytest.mark.django_db
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
    def test_invalid_data(
        self,
        setUp: Tuple[Client, str],
        data: Dict[str, Dict],
        error_messages: Dict[str, Dict],
    ) -> None:
        """
        This test is responsible for validating the expected behavior of the
        view when the request data is invalid and does not exist in the
        database.
        """

        # Simulating the request
        client, path = setUp
        response = client.post(
            path=path, data=data, content_type="application/json"
        )

        # Asserting that response data is correct
        assert response.status_code == 400
        assert response.data["code"] == "invalid_request_data"

        errors = response.data["detail"].copy()
        errors_formatted = {
            field: [str(error) for error in errors]
            for field, errors in errors.items()
        }

        for field, message in error_messages.items():
            assert errors_formatted[field] == message

    @pytest.mark.django_db
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
    def test_data_used(
        self,
        setUp: Tuple[Client, str],
        data: Dict[str, Dict],
        error_messages: Dict[str, Dict],
    ) -> None:
        """
        This test is responsible for validating the expected behavior of the
        view when the request data is invalid and exists in the database.
        """

        # Creating a user
        data_copy = data.copy()
        _ = User.objects.create_user(
            base_data={
                "email": data_copy["email"],
                "password": data_copy["password"],
            },
            role_data={
                "name": data_copy["name"],
                "last_name": data_copy["last_name"],
            },
            related_model_name=UserRoles.SEARCHER.value,
            is_active=False,
        )

        # Simulating the request
        client, path = setUp
        response = client.post(
            path=path, data=data, content_type="application/json"
        )

        # Asserting that response data is correct
        assert response.status_code == 400
        assert response.data["code"] == "invalid_request_data"

        errors = response.data["detail"].copy()
        errors_formatted = {
            field: [str(error) for error in errors]
            for field, errors in errors.items()
        }

        for field, message in error_messages.items():
            assert errors_formatted[field] == message

    @patch("apps.users.infrastructure.serializers.base.UserRepository")
    def test_exception_raised_db(
        self, user_repository_mock: Mock, setUp: Tuple[Client, str]
    ) -> None:
        """
        This test is responsible for validating the expected behavior of the
        view when a DatabaseConnectionError exception is raised.
        """

        # Mocking the methods of the UserRepository class
        # To control the behavior of serializer validations that use these methods
        # We make it return a DatabaseConnectionError exception
        get_user_data: Mock = user_repository_mock.get_user_data
        get_user_data.side_effect = DatabaseConnectionError

        # Simulating the request
        client, path = setUp
        response = client.post(
            path=path,
            data={
                "name": "Nombre del usuario",
                "last_name": "Apellido del usuario",
                "email": "user1@email.com",
                "password": "contraseña1234",
                "confirm_password": "contraseña1234",
            },
            content_type="application/json",
        )

        # Asserting that response data is correct
        assert response.status_code == 500
        assert response.data["code"] == "database_connection_error"
        assert (
            response.data["detail"]
            == "Unable to establish a connection with the database. Please try again later."
        )
