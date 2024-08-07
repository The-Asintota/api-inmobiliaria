from apps.users.infrastructure.serializers import (
    TokenObtainPairSerializer,
)
from apps.users.applications import JWTUsesCases
from apps.users.domain.constants import UserRoles
from apps.users.models import JWT, JWTBlacklist, User
from apps.api_exceptions import (
    DatabaseConnectionAPIError,
    PermissionDeniedAPIError,
    AuthenticationFailedAPIError,
)
from apps.utils import decode_jwt
from unittest.mock import Mock, patch
from typing import Callable, Tuple, Dict
import pytest


class TestApplication:
    """
    This class encapsulates all the tests for the use case in charge of authenticating
    users with JSON Web Token.
    """

    application_class = JWTUsesCases

    @pytest.mark.django_db
    def test_authenticated_user(
        self,
        create_user: Callable[[bool, str, bool], Tuple[User, Dict[str, Dict]]],
        setup_database: Callable,
    ) -> None:
        """
        This test is responsible for validating the expected behavior of the
        `authenticate_user` method when the user data is valid.
        """

        # Creating a user
        _, data = create_user(
            active=True, role=UserRoles.SEARCHER.value, add_perm=True
        )

        tokens = self.application_class(
            jwt_class=TokenObtainPairSerializer,
        ).authenticate_user(credentials=data["base_data"])

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
            .only("user__uuid", "jti", "token")
            .first()
        )
        refresh_obj = (
            JWT.objects.filter(jti=refresh_payload["jti"])
            .select_related("user")
            .only("user__uuid", "jti", "token")
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
        assert access_payload["role"] == UserRoles.SEARCHER.value
        assert refresh_payload["role"] == UserRoles.SEARCHER.value

    @pytest.mark.django_db
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

    @pytest.mark.django_db
    def test_if_inactive_user_account(
        self,
        create_user: Callable[[bool, str, bool], Tuple[User, Dict[str, Dict]]],
    ) -> None:
        """
        This test is responsible for validating the expected behavior of the
        `authenticate_user` method when the user account is inactive.
        """

        # Creating a user
        _, data = create_user(
            active=False, role=UserRoles.SEARCHER.value, add_perm=False
        )

        # Instantiating the application and calling the method
        with pytest.raises(AuthenticationFailedAPIError):
            _ = self.application_class(
                jwt_class=TokenObtainPairSerializer,
            ).authenticate_user(credentials=data["base_data"])

        # Asserting that the user does not exist in the database
        assert JWT.objects.count() == 0
        assert JWTBlacklist.objects.count() == 0

    @pytest.mark.django_db
    def test_if_user_has_not_permission(
        self,
        create_user: Callable[[bool, str, bool], Tuple[User, Dict[str, Dict]]],
        setup_database: Callable,
    ) -> None:
        """
        This test is responsible for validating the expected behavior of the
        `authenticate_user` method when the user account is inactive.
        """

        # Creating a user
        _, data = create_user(
            active=True, role=UserRoles.SEARCHER.value, add_perm=False
        )

        # Instantiating the application and calling the method
        with pytest.raises(PermissionDeniedAPIError):
            _ = self.application_class(
                jwt_class=TokenObtainPairSerializer,
            ).authenticate_user(credentials=data["base_data"])

        # Asserting that the user does not exist in the database
        assert JWT.objects.count() == 0
        assert JWTBlacklist.objects.count() == 0

    @patch("apps.backend.UserRepository")
    def test_exception_raised_db(
        self, user_repository_mock: Mock, jwt_class: Mock
    ) -> None:
        """
        This test is responsible for validating the expected behavior of the
        `authenticate_user` method when an exception is raised during the
        interaction with the database.
        """

        # Mocking the methods
        get_user_data: Mock = user_repository_mock.get_user_data
        get_token: Mock = jwt_class.get_token

        # Setting the return values
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
