from apps.users.domain.constants import (
    SearcherProperties,
    UserProperties,
)
from apps.api_exceptions import DatabaseConnectionAPIError
from apps.utils.messages import ERROR_MESSAGES
from tests.factory import UserFactory
from tests.utils import fake
from rest_framework import status
from django.test import Client
from django.urls import reverse
from unittest.mock import Mock, patch
from typing import Callable, Dict
import pytest


@pytest.mark.django_db
class TestSearcherRegisterUserAPIView:
    """
    This class encapsulates the tests for the view responsible for creating a
    user with the "Searcher" role.
    """

    path = reverse(viewname="searcher_user")
    user_factory = UserFactory
    client = Client()

    def test_if_valid_data(self, setup_database: Callable) -> None:
        """
        This test is responsible for validating the expected behavior of the
        view when the request data is valid.
        """

        # Creating the user data to be used in the test
        data = {
            "name": "Nombre del usuario",
            "last_name": "Apellido del usuario",
            "email": "user1@email.com",
            "password": "contraseña1234",
            "confirm_password": "contraseña1234",
        }

        # Simulating the request
        response = self.client.post(
            path=self.path, data=data, content_type="application/json"
        )

        # Asserting that response data is correct
        assert response.status_code == status.HTTP_201_CREATED

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
    def test_if_invalid_data(
        self,
        data: Dict[str, Dict],
        error_messages: Dict[str, Dict],
    ) -> None:
        """
        This test is responsible for validating the expected behavior of the
        view when the request data is invalid and does not exist in the database.
        """

        # Simulating the request
        response = self.client.post(
            path=self.path, data=data, content_type="application/json"
        )

        # Asserting that response data is correct
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["code"] == "invalid_request_data"

        errors_formatted = {
            field: [str(error) for error in errors]
            for field, errors in response.data["detail"].items()
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
    def test_data_used(
        self,
        data: Dict[str, Dict],
        error_messages: Dict[str, Dict],
    ) -> None:
        """
        This test is responsible for validating the expected behavior of the
        view when the request data is invalid and exists in the database.
        """

        # Creating the user
        _ = self.user_factory.searcher_user(
            email=data["email"],
            password=data["password"],
            name=data["name"],
            last_name=data["last_name"],
            active=False,
            save=True,
            add_perm=False,
        )

        # Simulating the request
        response = self.client.post(
            path=self.path, data=data, content_type="application/json"
        )

        # Asserting that response data is correct
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["code"] == "invalid_request_data"

        errors_formatted = {
            field: [str(error) for error in errors]
            for field, errors in response.data["detail"].items()
        }

        for field, message in error_messages.items():
            assert errors_formatted[field] == message

    @patch("apps.users.infrastructure.serializers.base.UserRepository")
    def test_if_conection_db_failed(self, user_repository_mock: Mock) -> None:
        """
        This test is responsible for validating the expected behavior of the
        view when a DatabaseConnectionAPIError exception is raised.
        """

        # Mocking the methods
        get_user_data: Mock = user_repository_mock.get_user_data
        get_user_data.side_effect = DatabaseConnectionAPIError

        # Creating the user data to be used in the test
        _, _, data = self.user_factory.searcher_user(
            active=False, save=False, add_perm=False
        )
        data["confirm_password"] = data["password"]

        # Simulating the request
        response = self.client.post(
            path=self.path, data=data, content_type="application/json"
        )

        # Asserting that response data is correct
        status_code_expected = DatabaseConnectionAPIError.status_code
        response_code_expected = DatabaseConnectionAPIError.default_code
        response_data_expected = DatabaseConnectionAPIError.default_detail

        assert response.status_code == status_code_expected
        assert response.data["code"] == response_code_expected
        assert response.data["detail"] == response_data_expected
