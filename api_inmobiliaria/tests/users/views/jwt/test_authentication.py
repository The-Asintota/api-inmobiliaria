from apps.users.applications.jwt import JWTErrorMessages
from apps.users.domain.constants import UserRoles
from apps.api_exceptions import (
    DatabaseConnectionAPIError,
    PermissionDeniedAPIError,
    AuthenticationFailedAPIError,
)
from tests.factory import UserFactory
from rest_framework import status
from django.test import Client
from django.urls import reverse
from unittest.mock import Mock, patch
from typing import Callable
import pytest


@pytest.mark.django_db
class TestAuthenticationAPIView:
    """
    This class encapsulates all the tests of the view in charge of handling
    authentication requests for users with JSON Web Token.

    A successful login will generate an access token and an update token for the user,
    provided their account is active and they have permission to authenticate using
    JSON Web Token.
    """

    path = reverse(viewname="jwt_authenticate_user")
    user_factory = UserFactory
    client = Client()

    @pytest.mark.parametrize(
        argnames="role",
        argvalues=[UserRoles.SEARCHER.value],
        ids=["searcher_user"],
    )
    def test_request_valid_data(
        self, role: str, setup_database: Callable
    ) -> None:
        """
        This test is responsible for validating the expected behavior of the view
        when the request data is valid.
        """

        # Creating the user data to be used in the test
        _, data = self.user_factory.create_user(
            role=role, active=True, save=True, add_perm=True
        )

        # Simulating the request
        credentials = {"email": data["email"], "password": data["password"]}
        response = self.client.post(
            path=self.path,
            data=credentials,
            content_type="application/json",
        )

        # Asserting that response data is correct
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

    def test_if_credentials_invalid(self) -> None:
        """
        This test is responsible for validating the expected behavior of the view
        when the credentials provided are invalid.
        """

        # Simulating the request
        credentials = {"email": "user1@emial.com", "password": "contraseña1234"}
        response = self.client.post(
            path=self.path,
            data=credentials,
            content_type="application/json",
        )

        # Asserting that response data is correct
        status_code_expected = AuthenticationFailedAPIError.status_code
        response_code_expected = AuthenticationFailedAPIError.default_code
        response_data_expected = JWTErrorMessages.AUTHENTICATION_FAILED.value

        assert response.status_code == status_code_expected
        assert response.data["code"] == response_code_expected
        assert response.data["detail"] == response_data_expected

    @pytest.mark.parametrize(
        argnames="role",
        argvalues=[UserRoles.SEARCHER.value],
        ids=["searcher_user"],
    )
    def test_if_inactive_user_account(
        self, role: str, setup_database: Callable
    ) -> None:
        """
        This test is responsible for validating the expected behavior of the view
        when the user account is inactive.
        """

        # Creating the user data to be used in the test
        _, data = self.user_factory.create_user(
            role=role, active=False, save=True, add_perm=True
        )

        # Simulating the request
        credentials = {"email": data["email"], "password": data["password"]}
        response = self.client.post(
            path=self.path,
            data=credentials,
            content_type="application/json",
        )

        # Asserting that response data is correct
        status_code_expected = AuthenticationFailedAPIError.status_code
        response_code_expected = AuthenticationFailedAPIError.default_code
        response_data_expected = JWTErrorMessages.INACTIVE_ACCOUNT.value

        assert response.status_code == status_code_expected
        assert response.data["code"] == response_code_expected
        assert response.data["detail"] == response_data_expected

    @pytest.mark.parametrize(
        argnames="role",
        argvalues=[UserRoles.SEARCHER.value],
        ids=["searcher_user"],
    )
    def test_if_user_has_not_permission(self, role: str) -> None:
        """
        This test is responsible for validating the expected behavior of the view
        when the user does not have the necessary permissions to perform the action.
        """

        # Creating the user data to be used in the test
        _, data = self.user_factory.create_user(
            role=role, active=True, save=True, add_perm=False
        )

        # Simulating the request
        credentials = {"email": data["email"], "password": data["password"]}
        response = self.client.post(
            path=self.path,
            data=credentials,
            content_type="application/json",
        )

        # Asserting that response data is correct
        status_code_expected = PermissionDeniedAPIError.status_code
        response_code_expected = PermissionDeniedAPIError.default_code
        response_data_expected = PermissionDeniedAPIError.default_detail

        assert response.status_code == status_code_expected
        assert response.data["code"] == response_code_expected
        assert response.data["detail"] == response_data_expected

    @patch("apps.backend.UserRepository")
    def test_if_conection_db_failed(self, user_repository_mock: Mock) -> None:
        """
        Test that validates the expected behavior of the view when the connection to
        the database fails.
        """

        # Mocking the methods
        get_user_data: Mock = user_repository_mock.get_user_data
        get_user_data.side_effect = DatabaseConnectionAPIError

        # Simulating the request
        credentials = {"email": "user1@emial.com", "password": "contraseña1234"}
        response = self.client.post(
            path=self.path,
            data=credentials,
            content_type="application/json",
        )

        # Asserting that response data is correct
        status_code_expected = DatabaseConnectionAPIError.status_code
        response_code_expected = DatabaseConnectionAPIError.default_code
        response_data_expected = DatabaseConnectionAPIError.default_detail

        assert response.status_code == status_code_expected
        assert response.data["code"] == response_code_expected
        assert response.data["detail"] == response_data_expected
