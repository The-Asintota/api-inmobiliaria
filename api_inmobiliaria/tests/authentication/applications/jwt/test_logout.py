from apps.authentication.applications import JWTLogout
from apps.authentication.models import JWTBlacklist
from apps.authentication.jwt import AccessToken
from apps.api_exceptions import DatabaseConnectionAPIError
from tests.factory import JWTFactory, UserFactory
from unittest.mock import Mock
import pytest


@pytest.mark.django_db
class TestLogoutApplication:
    """
    This class encapsulates all the tests of the JSON Web Token use case responsible
    for logging out a user.

    A successful logout will consist of invalidating the last JSON Web Tokens
    generated by the user, adding them to a blacklist if they have not yet expired, to
    prevent their further use.

    #### Clarifications:

    - The execution of this logic does not depend on the user role associated with the
    JSON Web Tokens. However, to simplify testing, the `seacher` role is used for
    users.
    - The execution of this logic does not depend on the user's permissions; that is,
    the user's permissions are not validated.
    """

    application_class = JWTLogout
    user_factory = UserFactory
    jwt_factory = JWTFactory

    def test_logout_user(self) -> None:
        """
        This test checks if the user is logged out correctly, adding the refresh token
        to the blacklist.
        """

        # Creating the JWTs to be used in the test
        base_user, _, _ = self.user_factory.searcher_user(
            active=True, save=True, add_perm=False
        )
        access_token_data = self.jwt_factory.access(
            user_role=base_user.content_type.model,
            user=base_user,
            exp=False,
            save=True,
        )
        access_token = AccessToken(payload=access_token_data["payload"])

        # Asserting the tokens are not in the blacklist
        assert JWTBlacklist.objects.count() == 0

        # Instantiating the application
        self.application_class.logout_user(access_token=access_token)

        # Assert that the refresh token was added to the blacklist
        assert JWTBlacklist.objects.filter(
            token__jti=access_token.payload["jti"]
        ).exists()

    def test_if_conection_db_failed(self) -> None:
        """
        Test that validates the expected behavior of the use case when the connection
        to the database fails.
        """

        # Mocking the methods
        access_token = Mock()
        blacklist: Mock = access_token.blacklist
        blacklist.side_effect = DatabaseConnectionAPIError

        # Instantiating the application
        with pytest.raises(DatabaseConnectionAPIError):
            self.application_class.logout_user(access_token=access_token)

        # Assert that the refresh token was not added to the blacklist
        assert JWTBlacklist.objects.count() == 0
