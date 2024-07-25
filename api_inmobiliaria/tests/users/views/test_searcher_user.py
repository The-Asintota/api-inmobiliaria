from apps.users.domain.constants import SearcherUser
from apps.users.models import User, UserRoles
from apps.exceptions import DatabaseConnectionError
from apps.utils import ERROR_MESSAGES
from django.test import Client
from django.urls import reverse
from unittest.mock import Mock, patch
from typing import Tuple, Dict
from faker import Faker
import pytest


fake = Faker("es_CO")


@pytest.fixture
def setUp() -> Tuple[Client, str]:

    return Client(), reverse(viewname="searcher_user")


class TestAPIViewPOSTMethod:
    """
    This class groups all test cases for the POST method of the `SearcherUserAPIView`.
    The view is responsible for managing the registration of new users with the
    `searcheruser` role.
    """

    @staticmethod
    def _assert_errors_nested_field(
        key: str, value: Dict, expected_errors: Dict[str, Dict]
    ) -> None:
        """
        This method asserts the errors of a nested field in the serializer.

        #### Parameters:
        - key: The key of the nested field.
        - value: The errors of the nested field.
        - expected_errors: The expected errors of the nested field.
        """

        profile_data_errors_formatted = {
            field: [str(error) for error in errors]
            for field, errors in value.items()
        }

        for field, message in expected_errors[key].items():
            assert profile_data_errors_formatted[field] == message

    @pytest.mark.django_db
    def test_request_valid(self, setUp: Tuple[Client, str]) -> None:
        data = {
            "full_name": "Nombre Apellido",
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
    def test_invalid_data(
        self,
        setUp: Tuple[Client, str],
        data: Dict[str, Dict],
        error_messages: Dict[str, Dict],
    ) -> None:
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
    def test_data_used(
        self,
        setUp: Tuple[Client, str],
        data: Dict[str, Dict],
        error_messages: Dict[str, Dict],
    ) -> None:
        # Creating a user
        data_copy = data.copy()
        _ = User.objects.create_user(
            base_data={
                "email": data_copy["email"],
                "password": data_copy["password"],
            },
            profile_data={"full_name": data_copy["full_name"]},
            related_model_name=UserRoles.SEARCHER.value,
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
        # Mocking the methods
        get: Mock = user_repository_mock.get

        # Setting the return values
        get.side_effect = DatabaseConnectionError

        # Simulating the request
        client, path = setUp
        response = client.post(
            path=path,
            data={
                "full_name": "Nombre Apellido",
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
