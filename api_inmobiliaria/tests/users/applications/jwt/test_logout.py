from apps.users.applications import JWTLogout
from apps.api_exceptions import DatabaseConnectionAPIError
from authentication.jwt import AccessToken, RefreshToken
from tests.factory import JWTFactory, UserFactory
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
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
        user, _, _ = self.user_factory.searcher_user(
            active=True, save=True, add_perm=False
        )
        jwt_data = self.jwt_factory.access_and_refresh(
            user_role=user.content_type.model,
            user=user,
            exp_access=False,
            exp_refresh=False,
            save=True,
        )
        access_token = AccessToken(payload=jwt_data["payloads"]["access_token"])
        refresh_token = RefreshToken(
            payload=jwt_data["payloads"]["refresh_token"]
        )

        # Asserting the tokens are not in the blacklist
        assert BlacklistedToken.objects.count() == 0

        # Instantiating the application
        self.application_class.logout_user(
            data={"refresh_token": refresh_token, "access_token": access_token},
        )

        # Assert that the refresh token was added to the blacklist
        assert BlacklistedToken.objects.filter(
            token__jti=refresh_token.payload["jti"]
        ).exists()
        assert BlacklistedToken.objects.filter(
            token__jti=access_token.payload["jti"]
        ).exists()

    def test_if_conection_db_failed(self) -> None:
        """
        Test that validates the expected behavior of the use case when the connection
        to the database fails.
        """

        # Mocking the methods
        access_token = Mock()
        refresh_token = Mock()
        blacklist = refresh_token.blacklist
        blacklist.side_effect = DatabaseConnectionAPIError

        # Instantiating the application
        with pytest.raises(DatabaseConnectionAPIError):
            self.application_class.logout_user(
                data={
                    "refresh_token": refresh_token,
                    "access_token": access_token,
                },
            )

        # Assert that the refresh token was not added to the blacklist
        assert BlacklistedToken.objects.count() == 0
