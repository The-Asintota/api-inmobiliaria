from apps.users.infrastructure.serializers import (
    TokenObtainPairSerializer,
)
from apps.users.applications import JWTUsesCases
from apps.users.domain.constants import UserRoles
from apps.users.models import JWT, JWTBlacklist
from apps.api_exceptions import (
    DatabaseConnectionAPIError,
    PermissionDeniedAPIError,
    AuthenticationFailedAPIError,
)
from apps.utils import decode_jwt
from tests.factory import UserFactory
from unittest.mock import Mock, patch
from typing import Callable
import pytest


@pytest.mark.django_db
class TestAuthenticationApplication:
    """
    This class encapsulates all the tests for the use case in charge of authenticating
    users with JSON Web Token.

    A successful login will generate an access token and an update token for the user,
    provided their account is active and they have permission to authenticate using
    JSON Web Token.
    """

    application_class = JWTUsesCases
    user_factory = UserFactory

    @pytest.mark.parametrize(
        argnames="role",
        argvalues=[UserRoles.SEARCHER.value],
        ids=["searcher_user"],
    )
    def test_authenticated_user(
        self, role: str, setup_database: Callable
    ) -> None:
        """
        This test is responsible for validating the expected behavior of the
        `authenticate_user` method when the user data is valid.
        """

        # Creating the user data to be used in the test
        _, data = self.user_factory.create_user(
            role=role, active=True, save=True, add_perm=True
        )

        tokens = self.application_class(
            jwt_class=TokenObtainPairSerializer,
        ).authenticate_user(
            credentials={
                "email": data["email"],
                "password": data["password"],
            }
        )

        # Asserting that the tokens were generated
        access = tokens.get("access", False)
        refresh = tokens.get("refresh", False)

        assert access
        assert refresh

        # Assert that the generated tokens were saved in the database
        access_payload = decode_jwt(token=access)
        refresh_payload = decode_jwt(token=refresh)

        access_obj = (
            JWT.objects.filter(jti=access_payload["jti"])
            .select_related("user")
            .first()
        )
        refresh_obj = (
            JWT.objects.filter(jti=refresh_payload["jti"])
            .select_related("user")
            .first()
        )

        assert access_obj
        assert refresh_obj
        assert JWTBlacklist.objects.count() == 0

        # Asserting that the tokens were created with the correct data
        assert access_obj.user.uuid.__str__() == access_payload["user_uuid"]
        assert access_obj.jti == access_payload["jti"]
        assert access_obj.token == tokens["access"]
        assert refresh_obj.user.uuid.__str__() == refresh_payload["user_uuid"]
        assert refresh_obj.jti == refresh_payload["jti"]
        assert refresh_obj.token == tokens["refresh"]
        assert access_payload["role"] == role
        assert refresh_payload["role"] == role

    def test_if_credentials_invalid(self) -> None:
        """
        This test is responsible for validating the expected behavior of the
        `authenticate_user` method when the user data is invalid.
        """

        # Instantiating the application and calling the method
        with pytest.raises(AuthenticationFailedAPIError):
            _ = self.application_class(
                jwt_class=TokenObtainPairSerializer,
            ).authenticate_user(
                credentials={
                    "email": "user1@email.com",
                    "password": "contraseña1234",
                }
            )

        # Asserting that the user does not exist in the database
        assert JWT.objects.count() == 0
        assert JWTBlacklist.objects.count() == 0

    @pytest.mark.parametrize(
        argnames="role",
        argvalues=[UserRoles.SEARCHER.value],
        ids=["searcher_user"],
    )
    def test_if_inactive_user_account(
        self, role: str, setup_database: Callable
    ) -> None:
        """
        This test is responsible for validating the expected behavior of the
        `authenticate_user` method when the user account is inactive.
        """

        # Creating the user data to be used in the test
        _, data = self.user_factory.create_user(
            role=role, active=False, save=True, add_perm=True
        )

        # Instantiating the application and calling the method
        with pytest.raises(AuthenticationFailedAPIError):
            _ = self.application_class(
                jwt_class=TokenObtainPairSerializer,
            ).authenticate_user(
                credentials={
                    "email": data["email"],
                    "password": data["password"],
                }
            )

        # Asserting that the user does not exist in the database
        assert JWT.objects.count() == 0
        assert JWTBlacklist.objects.count() == 0

    @pytest.mark.parametrize(
        argnames="role",
        argvalues=[UserRoles.SEARCHER.value],
        ids=["searcher_user"],
    )
    def test_if_user_has_not_permission(self, role: str) -> None:
        """
        This test is responsible for validating the expected behavior of the
        `authenticate_user` method when the user account is inactive.
        """

        # Creating the user data to be used in the test
        _, data = self.user_factory.create_user(
            role=role, active=True, save=True, add_perm=False
        )

        # Instantiating the application and calling the method
        with pytest.raises(PermissionDeniedAPIError):
            _ = self.application_class(
                jwt_class=TokenObtainPairSerializer,
            ).authenticate_user(
                credentials={
                    "email": data["email"],
                    "password": data["password"],
                }
            )

        # Asserting that the user does not exist in the database
        assert JWT.objects.count() == 0
        assert JWTBlacklist.objects.count() == 0

    @patch("apps.backend.UserRepository")
    def test_if_conection_db_failed(
        self, user_repository_mock: Mock, jwt_class: Mock
    ) -> None:
        """
        Test that validates the expected behavior of the view when the connection to
        the database fails.
        """

        # Mocking the methods
        get_user_data: Mock = user_repository_mock.get_user_data
        get_token: Mock = jwt_class.get_token
        get_user_data.side_effect = DatabaseConnectionAPIError

        # Instantiating the application and calling the method
        with pytest.raises(DatabaseConnectionAPIError):
            _ = self.application_class(
                jwt_class=jwt_class,
            ).authenticate_user(
                credentials={
                    "email": "user1@email.com",
                    "password": "contraseña1234",
                }
            )

        # Asserting that the methods were not called
        get_token.assert_not_called()
