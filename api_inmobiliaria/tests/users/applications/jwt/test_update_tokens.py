from apps.users.infrastructure.db import JWTRepository, UserRepository
from apps.users.applications import JWTUpdate
from apps.users.models import BaseUser
from apps.users.domain.constants import UserRoles
from apps.api_exceptions import (
    DatabaseConnectionAPIError,
    ResourceNotFoundAPIError,
)
from authentication.jwt import RefreshToken
from settings.environments.base import SIMPLE_JWT
from tests.factory import JWTFactory, UserFactory
from tests.utils import empty_queryset
from rest_framework_simplejwt.token_blacklist.models import (
    OutstandingToken,
    BlacklistedToken,
)
from unittest.mock import Mock
from jwt import decode
import pytest


@pytest.mark.django_db
class TestUpdateTokensApplication:
    """
    This class encapsulates all the tests of the JWT use case responsible for updating
    the tokens of a user.

    #### Clarifications:

    - To facilitate certain tests focused on the validation of JSON Web Tokens, a user
    with the role `searcher` is used, since these validations are not dependent on the
    user's role.
    - The execution of this logic does not depend on the user's permissions; that is,
    the user's permissions are not validated.
    """

    application_class = JWTUpdate
    user_factory = UserFactory
    jwt_factory = JWTFactory

    @pytest.mark.parametrize(
        argnames="user_role",
        argvalues=[UserRoles.SEARCHER.value],
        ids=["searcher_user"],
    )
    def test_updated_tokens(self, user_role: str) -> None:
        """
        This test case is responsible for testing the successful update of the tokens
        of a user.
        """

        # Creating the JWTs to be used in the test
        user, _, _ = self.user_factory.user(
            user_role=user_role, active=True, save=True, add_perm=False
        )
        refresh_data = self.jwt_factory.refresh(
            user_role=user.content_type.model,
            user=user,
            exp=False,
            save=True,
        )
        refresh_token = RefreshToken(payload=refresh_data["payload"])

        # Instantiating the application
        app = self.application_class(
            user_repository=UserRepository,
            jwt_repository=JWTRepository,
        )
        tokens = app.new_tokens(refresh_token=refresh_token)

        # Asserting that the tokens were generated
        response_access_token = tokens.get("access_token", False)
        response_refresh_token = tokens.get("refresh_token", False)

        assert response_access_token
        assert response_refresh_token

        # Assert that the refresh token was added to the blacklist
        assert BlacklistedToken.objects.filter(
            token__jti=refresh_token.payload["jti"]
        ).exists()

        # Assert that the generated tokens were saved in the database
        response_access_payload = decode(
            jwt=response_access_token,
            key=SIMPLE_JWT["SIGNING_KEY"],
            algorithms=[SIMPLE_JWT["ALGORITHM"]],
        )
        response_refresh_payload = decode(
            jwt=response_refresh_token,
            key=SIMPLE_JWT["SIGNING_KEY"],
            algorithms=[SIMPLE_JWT["ALGORITHM"]],
        )
        access_obj = (
            OutstandingToken.objects.filter(jti=response_access_payload["jti"])
            .select_related("user")
            .first()
        )
        refresh_obj = (
            OutstandingToken.objects.filter(jti=response_refresh_payload["jti"])
            .select_related("user")
            .first()
        )

        assert access_obj
        assert refresh_obj

        # Asserting that the tokens were created with the correct data
        assert (
            access_obj.user.uuid.__str__()
            == response_access_payload["user_uuid"]
        )
        assert access_obj.jti == response_access_payload["jti"]
        assert access_obj.token == tokens["access_token"]
        assert (
            refresh_obj.user.uuid.__str__()
            == response_refresh_payload["user_uuid"]
        )
        assert refresh_obj.jti == response_refresh_payload["jti"]
        assert refresh_obj.token == tokens["refresh_token"]
        assert response_access_payload["user_role"] == user_role
        assert response_refresh_payload["user_role"] == user_role

    def test_if_token_not_found(self) -> None:
        """
        This test is responsible for validating the expected behavior of the use case
        when the JWTs are not found in the database.
        """

        # Creating the JWTs to be used in the test
        user, _, _ = self.user_factory.searcher_user(
            active=True, save=True, add_perm=False
        )
        refresh_data = self.jwt_factory.refresh(
            user_role=user.content_type.model,
            user=user,
            exp=False,
            save=False,
        )
        refresh_token = RefreshToken(payload=refresh_data["payload"])

        # Instantiating the application
        with pytest.raises(ResourceNotFoundAPIError):
            app = self.application_class(
                user_repository=UserRepository,
                jwt_repository=JWTRepository,
            )
            _ = app.new_tokens(refresh_token=refresh_token)

        # Asserting that the tokens were not generated
        assert OutstandingToken.objects.count() == 0

        # Assert that the refresh token was not added to the blacklist
        assert BlacklistedToken.objects.count() == 0

    def test_if_user_not_found(self, user_repository: Mock) -> None:
        """
        This test is responsible for validating the expected behavior of the use case
        when the user is not found in the database.
        """

        # Mocking the methods
        get_base_data: Mock = user_repository.get_base_data
        get_base_data.return_value = empty_queryset(model=BaseUser)

        # Creating the JWTs to be used in the test
        refresh_data = self.jwt_factory.refresh(
            user_role="AnyUser",
            user=BaseUser(),
            exp=False,
            save=False,
        )
        refresh_token = RefreshToken(payload=refresh_data["payload"])

        # Instantiating the application
        with pytest.raises(ResourceNotFoundAPIError):
            app = self.application_class(
                user_repository=user_repository,
                jwt_repository=JWTRepository,
            )
            _ = app.new_tokens(refresh_token=refresh_token)

        # Asserting that the tokens were not generated
        assert OutstandingToken.objects.count() == 0

        # Assert that the refresh token was not added to the blacklist
        assert BlacklistedToken.objects.count() == 0

    def test_if_conection_db_failed(self, user_repository: Mock) -> None:
        """
        Test that validates the expected behavior of the use case when the connection
        to the database fails.
        """

        # Mocking the methods
        get_base_data: Mock = user_repository.get_base_data
        get_base_data.side_effect = DatabaseConnectionAPIError

        # Creating the JWTs to be used in the test
        refresh_data = self.jwt_factory.refresh(
            user_role="AnyUser",
            user=BaseUser(),
            exp=False,
            save=False,
        )
        refresh_token = RefreshToken(payload=refresh_data["payload"])

        # Instantiating the application
        with pytest.raises(DatabaseConnectionAPIError):
            app = self.application_class(
                user_repository=user_repository,
                jwt_repository=JWTRepository,
            )
            _ = app.new_tokens(refresh_token=refresh_token)

        # Asserting that the tokens were not generated
        assert OutstandingToken.objects.count() == 0

        # Assert that the refresh token was not added to the blacklist
        assert BlacklistedToken.objects.count() == 0
