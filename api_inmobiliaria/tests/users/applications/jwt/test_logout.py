from apps.users.infrastructure.db import JWTRepository, UserRepository
from apps.users.applications import JWTUsesCases
from apps.users.models import User, JWTBlacklist, JWT
from apps.api_exceptions import (
    DatabaseConnectionAPIError,
    ResourceNotFoundAPIError,
    JWTAPIError,
)
from tests.factory import JWTFactory, UserFactory
from tests.utils import empty_queryset
from unittest.mock import Mock
import pytest


@pytest.mark.django_db
class TestLogoutApplication:
    """
    This class encapsulates all the tests of the JSON Web Token use case responsible
    for logging out a user, this logic is executed regardless of the user's role.

    A successful logout will consist of invalidating the last JSON Web Tokens
    generated by the user, adding them to a blacklist if they have not yet expired, to
    prevent their further use.
    """

    application_class = JWTUsesCases
    user_factory = UserFactory
    jwt_factory = JWTFactory

    def test_logout_user(self) -> None:
        """
        This test checks if the user is logged out correctly, adding the refresh token
        to the blacklist.
        """

        # Creating the user data and the JWTs to be used in the test
        user, _ = self.user_factory.create_searcher_user(
            active=True, save=True, add_perm=False
        )
        jwt_data = self.jwt_factory.access_and_refresh(
            user=user,
            role="AnyUser",
            exp_access=False,
            exp_refresh=False,
            save=True,
        )

        # Asserting the tokens are not in the blacklist
        assert JWTBlacklist.objects.count() == 0

        # Instantiating the application
        self.application_class(
            user_repository=UserRepository,
            jwt_repository=JWTRepository,
        ).logout_user(data=jwt_data["payloads"])

        # Assert that the refresh token was added to the blacklist
        assert JWTBlacklist.objects.filter(
            token__jti=jwt_data["payloads"]["refresh"]["jti"]
        ).exists()
        assert JWTBlacklist.objects.filter(
            token__jti=jwt_data["payloads"]["access"]["jti"]
        ).exists()

    def test_if_token_not_found(
        self, user_repository: Mock, jwt_repository: Mock
    ) -> None:
        """
        This test checks if the application raises an exception when the JWT is not
        found.
        """

        # Creating the user data and the JWTs to be used in the test
        user, _ = self.user_factory.create_searcher_user(
            active=True, save=True, add_perm=False
        )
        jwt_data = self.jwt_factory.access_and_refresh(
            user=user,
            role="AnyUser",
            exp_access=False,
            exp_refresh=False,
            save=False,
        )

        # Mocking the methods
        get_user_data: Mock = user_repository.get_user_data
        first: Mock = get_user_data.first
        get_jwt: Mock = jwt_repository.get
        add_to_blacklist: Mock = jwt_repository.add_to_blacklist
        add_to_checklist: Mock = jwt_repository.add_to_checklist
        get_jwt.return_value = empty_queryset(model=JWT)
        first.return_value = User

        # Instantiating the application
        with pytest.raises(ResourceNotFoundAPIError):
            self.application_class(
                user_repository=user_repository,
                jwt_repository=jwt_repository,
            ).logout_user(data=jwt_data["payloads"])

        # Asserting that the methods not called
        add_to_blacklist.assert_not_called()
        add_to_checklist.assert_not_called()

    def test_if_tokens_not_match_user_last_tokens(self) -> None:
        """
        This test is responsible for validating the expected behavior of the view
        when the JWTs do not match the user's last tokens.
        """

        # Creating the user data and the JWTs to be used in the test
        user, _ = self.user_factory.create_searcher_user(
            active=True, save=True, add_perm=False
        )
        jwt_data = self.jwt_factory.access_and_refresh(
            user=user,
            role="AnyUser",
            exp_access=False,
            exp_refresh=False,
            save=True,
        )

        # Other tokens are created in order to raise the exception
        _ = self.jwt_factory.access_and_refresh(
            user=user,
            role="AnyUser",
            exp_access=False,
            exp_refresh=False,
            save=True,
        )

        # Instantiating the application
        with pytest.raises(JWTAPIError):
            self.application_class(
                user_repository=UserRepository,
                jwt_repository=JWTRepository,
            ).logout_user(data=jwt_data["payloads"])

        # Assert that the refresh token was not added to the blacklist
        assert JWTBlacklist.objects.count() == 0

    def test_if_user_not_found(
        self, user_repository: Mock, jwt_repository: Mock
    ) -> None:
        """
        This test checks if the application raises an exception when the user is not
        found.
        """

        # Mocking the methods
        get_user_data: Mock = user_repository.get_user_data
        get_jwt: Mock = jwt_repository.get
        add_to_blacklist: Mock = jwt_repository.add_to_blacklist
        add_to_checklist: Mock = jwt_repository.add_to_checklist
        get_user_data.return_value = empty_queryset(model=User)

        # Creating the JWTs to be used in the test
        jwt_data = self.jwt_factory.access_and_refresh(
            user=User(),
            role="AnyUser",
            exp_access=False,
            exp_refresh=False,
            save=False,
        )

        # Instantiating the application
        with pytest.raises(ResourceNotFoundAPIError):
            self.application_class(
                user_repository=user_repository,
                jwt_repository=jwt_repository,
            ).logout_user(data=jwt_data["payloads"])

        # Asserting that the methods not called
        get_jwt.assert_not_called()
        add_to_blacklist.assert_not_called()
        add_to_checklist.assert_not_called()

    def test_if_conection_db_failed(
        self, user_repository: Mock, jwt_repository: Mock
    ) -> None:
        """
        Test that validates the expected behavior of the view when the connection to
        the database fails.
        """

        # Mocking the methods
        get_user_data: Mock = user_repository.get_user_data
        get_jwt: Mock = jwt_repository.get
        add_to_blacklist: Mock = jwt_repository.add_to_blacklist
        add_to_checklist: Mock = jwt_repository.add_to_checklist
        get_user_data.side_effect = DatabaseConnectionAPIError

        # Creating the JWTs to be used in the test
        jwt_data = self.jwt_factory.access_and_refresh(
            user=User(),
            role="AnyUser",
            exp_access=False,
            exp_refresh=False,
            save=False,
        )

        # Instantiating the application
        with pytest.raises(DatabaseConnectionAPIError):
            self.application_class(
                user_repository=user_repository,
                jwt_repository=jwt_repository,
            ).logout_user(data=jwt_data["payloads"])

        # Asserting that the methods not called
        get_jwt.assert_not_called()
        add_to_blacklist.assert_not_called()
        add_to_checklist.assert_not_called()