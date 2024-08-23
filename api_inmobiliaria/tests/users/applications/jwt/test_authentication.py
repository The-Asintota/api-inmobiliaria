from apps.users.applications import JWTLogin
from apps.users.domain.constants import UserRoles
from apps.api_exceptions import (
    DatabaseConnectionAPIError,
    PermissionDeniedAPIError,
    AuthenticationFailedAPIError,
)
from settings.environments.base import SIMPLE_JWT
from tests.factory import UserFactory
from rest_framework_simplejwt.token_blacklist.models import (
    OutstandingToken,
    BlacklistedToken,
)
from unittest.mock import Mock, patch
from typing import Callable
from jwt import decode
import pytest


@pytest.mark.django_db
class TestLoginApplication:
    """
    This class encapsulates all the tests for the use case in charge of authenticating
    users with JSON Web Token.

    A successful login will generate an access token and an update token for the user,
    provided their account is active and they have permission to authenticate using
    JSON Web Token.
    """

    application_class = JWTLogin
    user_factory = UserFactory

    @pytest.mark.parametrize(
        argnames="role_user",
        argvalues=[UserRoles.SEARCHER.value],
        ids=["searcher_user"],
    )
    def test_authenticated_user(
        self, role_user: str, setup_database: Callable
    ) -> None:
        """
        This test is responsible for validating the expected behavior of the use case
        when the request data is valid.
        """

        # Creating the user data to be used in the test
        _, _, data = self.user_factory.user(
            role_user=role_user, active=True, save=True, add_perm=True
        )

        response_data = self.application_class.authenticate_user(
            credentials={
                "email": data["email"],
                "password": data["password"],
            }
        )

        # Asserting that the tokens were generated
        access = response_data.get("access_token", False)
        refresh = response_data.get("refresh_token", False)

        assert access
        assert refresh

        # Assert that the generated tokens were saved in the database
        access_payload = decode(
            jwt=access,
            key=SIMPLE_JWT["SIGNING_KEY"],
            algorithms=[SIMPLE_JWT["ALGORITHM"]],
        )
        refresh_payload = decode(
            jwt=refresh,
            key=SIMPLE_JWT["SIGNING_KEY"],
            algorithms=[SIMPLE_JWT["ALGORITHM"]],
        )

        access_obj = (
            OutstandingToken.objects.filter(jti=access_payload["jti"])
            .select_related("user")
            .first()
        )
        refresh_obj = (
            OutstandingToken.objects.filter(jti=refresh_payload["jti"])
            .select_related("user")
            .first()
        )

        assert access_obj
        assert refresh_obj
        assert BlacklistedToken.objects.count() == 0

        # Asserting that the tokens were created with the correct data
        assert access_obj.user.uuid.__str__() == access_payload["user_uuid"]
        assert access_obj.jti == access_payload["jti"]
        assert access_obj.token == response_data["access_token"]
        assert refresh_obj.user.uuid.__str__() == refresh_payload["user_uuid"]
        assert refresh_obj.jti == refresh_payload["jti"]
        assert refresh_obj.token == response_data["refresh_token"]
        assert access_payload["role_user"] == role_user
        assert refresh_payload["role_user"] == role_user
        assert response_data["role_user"] == role_user

    def test_if_credentials_invalid(self) -> None:
        """
        This test is responsible for validating the expected behavior of the use case
        when the credentials provided are invalid.
        """

        # Instantiating the application and calling the method
        with pytest.raises(AuthenticationFailedAPIError):
            _ = self.application_class.authenticate_user(
                credentials={
                    "email": "user1@email.com",
                    "password": "contraseña1234",
                }
            )

        # Asserting that the user does not exist in the database
        assert OutstandingToken.objects.count() == 0
        assert BlacklistedToken.objects.count() == 0

    @pytest.mark.parametrize(
        argnames="role_user",
        argvalues=[UserRoles.SEARCHER.value],
        ids=["searcher_user"],
    )
    def test_if_inactive_user_account(
        self, role_user: str, setup_database: Callable
    ) -> None:
        """
        This test is responsible for validating the expected behavior of the use case
        when the user account is inactive.
        """

        # Creating the user data to be used in the test
        _, _, data = self.user_factory.user(
            role_user=role_user, active=False, save=True, add_perm=True
        )

        # Instantiating the application and calling the method
        with pytest.raises(AuthenticationFailedAPIError):
            _ = self.application_class.authenticate_user(
                credentials={
                    "email": data["email"],
                    "password": data["password"],
                }
            )

        # Asserting that the user does not exist in the database
        assert OutstandingToken.objects.count() == 0
        assert BlacklistedToken.objects.count() == 0

    @pytest.mark.parametrize(
        argnames="role_user",
        argvalues=[UserRoles.SEARCHER.value],
        ids=["searcher_user"],
    )
    def test_if_user_has_not_permission(self, role_user: str) -> None:
        """
        This test is responsible for validating the expected behavior of the use case
        when the user does not have the necessary permissions to perform the action.
        """

        # Creating the user data to be used in the test
        _, _, data = self.user_factory.user(
            role_user=role_user, active=True, save=True, add_perm=False
        )

        # Instantiating the application and calling the method
        with pytest.raises(PermissionDeniedAPIError):
            _ = self.application_class.authenticate_user(
                credentials={
                    "email": data["email"],
                    "password": data["password"],
                }
            )

        # Asserting that the user does not exist in the database
        assert OutstandingToken.objects.count() == 0
        assert BlacklistedToken.objects.count() == 0

    @patch("apps.backend.UserRepository")
    def test_if_conection_db_failed(self, user_repository_mock: Mock) -> None:
        """
        Test that validates the expected behavior of the use case when the connection
        to the database fails.
        """

        # Mocking the methods
        get_user_data: Mock = user_repository_mock.get_user_data
        get_user_data.side_effect = DatabaseConnectionAPIError

        # Instantiating the application and calling the method
        with pytest.raises(DatabaseConnectionAPIError):
            _ = self.application_class.authenticate_user(
                credentials={
                    "email": "user1@email.com",
                    "password": "contraseña1234",
                }
            )

        # Asserting that the user does not exist in the database
        assert OutstandingToken.objects.count() == 0
        assert BlacklistedToken.objects.count() == 0
