from apps.users.models import UserRoles
from apps.exceptions import DatabaseConnectionError
from django.test import Client
from django.urls import reverse
from unittest.mock import Mock, patch
from typing import Tuple
import pytest


@pytest.fixture
def setUp() -> Tuple[Client, str]:

    return Client(), reverse(viewname="jwt_authenticate_user")


class TestAPIView:

    @pytest.mark.django_db
    def test_request_valid(
        self, setUp: Tuple[Client, str], save_user_db
    ) -> None:
        # Creating a user
        _, data = save_user_db(active=True, role=UserRoles.SEARCHER.value)

        # Simulating the request
        client, path = setUp
        response = client.post(
            path=path,
            data={"email": data["email"], "password": data["password"]},
            content_type="application/json",
        )

        # Asserting that response data is correct
        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data

    @pytest.mark.django_db
    def test_if_credentials_invalid(self, setUp: Tuple[Client, str]) -> None:
        # Simulating the request
        client, path = setUp
        response = client.post(
            path=path,
            data={"email": "user1@emial.com", "password": "contraseña1234"},
            content_type="application/json",
        )

        # Asserting that response data is correct
        assert response.status_code == 401
        assert "authentication_failed" in response.data["code"]
        assert "Credenciales inválidas." in response.data["detail"]

    @pytest.mark.django_db
    def test_if_inactive_user_account(
        self, setUp: Tuple[Client, str], save_user_db
    ) -> None:
        # Creating a user
        _, data = save_user_db(active=False, role=UserRoles.SEARCHER.value)

        # Simulating the request
        client, path = setUp
        response = client.post(
            path=path,
            data={"email": data["email"], "password": data["password"]},
            content_type="application/json",
        )

        # Asserting that response data is correct
        assert response.status_code == 401
        assert "authentication_failed" in response.data["code"]
        assert "Cuenta del usuario inactiva." in response.data["detail"]

    @patch("apps.users.backend.UserRepository")
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
            data={"email": "user1@emial.com", "password": "contraseña1234"},
            content_type="application/json",
        )

        # Asserting that response data is correct
        assert response.status_code == 500
        assert "database_connection_error" in response.data["code"]
        assert (
            "Unable to establish a connection with the database. Please try again later."
            in response.data["detail"]
        )
