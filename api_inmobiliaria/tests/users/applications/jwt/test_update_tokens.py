from apps.users.infrastructure.serializers import TokenObtainPairSerializer
from apps.users.infrastructure.db import JWTRepository, UserRepository
from apps.users.applications import JWTUsesCases
from apps.users.models import User, JWT, JWTBlacklist
from apps.users.domain.constants import UserRoles
from apps.api_exceptions import (
    DatabaseConnectionAPIError,
    ResourceNotFoundAPIError,
    JWTAPIError,
)
from apps.utils import decode_jwt
from tests.factory import JWTFactory, UserFactory
from tests.utils import empty_queryset
from unittest.mock import Mock
import pytest


@pytest.mark.django_db
class TestUpdateTokensApplication:
    """
    This class encapsulates all the tests of the JWT use case responsible for updating
    the tokens of a user.
    """

    application_class = JWTUsesCases
    user_factory = UserFactory
    jwt_factory = JWTFactory

    @pytest.mark.parametrize(
        argnames="role",
        argvalues=[UserRoles.SEARCHER.value],
        ids=["searcher_user"],
    )
    def test_updated_tokens(self, role: str) -> None:
        """
        This test case is responsible for testing the successful update of the tokens
        of a user.
        """

        # Creating the user data and the JWTs to be used in the test
        user, _ = self.user_factory.create_user(
            role=role, active=True, save=True, add_perm=False
        )
        jwt_data = self.jwt_factory.access_and_refresh(
            user=user,
            role=role,
            exp_access=True,
            exp_refresh=False,
            save=True,
        )

        # Instantiating the application
        tokens = self.application_class(
            user_repository=UserRepository,
            jwt_repository=JWTRepository,
            jwt_class=TokenObtainPairSerializer,
        ).update_tokens(data=jwt_data["payloads"])

        # Asserting that the tokens were generated
        access = tokens.get("access", False)
        refresh = tokens.get("refresh", False)

        assert access
        assert refresh

        # Assert that the refresh token was added to the blacklist
        assert JWTBlacklist.objects.filter(
            token__jti=jwt_data["payloads"]["refresh"]["jti"]
        ).exists()
        assert not JWTBlacklist.objects.filter(
            token__jti=jwt_data["payloads"]["access"]["jti"]
        ).exists()

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

        # Asserting that the tokens were created with the correct data
        assert access_obj.user.uuid.__str__() == access_payload["user_uuid"]
        assert access_obj.jti == access_payload["jti"]
        assert access_obj.token == tokens["access"]
        assert refresh_obj.user.uuid.__str__() == refresh_payload["user_uuid"]
        assert refresh_obj.jti == refresh_payload["jti"]
        assert refresh_obj.token == tokens["refresh"]
        assert access_payload["role"] == role
        assert refresh_payload["role"] == role

    def test_if_token_not_found(self) -> None:
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
            exp_access=True,
            exp_refresh=False,
            save=False,
        )

        # Instantiating the application
        with pytest.raises(ResourceNotFoundAPIError):
            _ = self.application_class(
                user_repository=UserRepository,
                jwt_repository=JWTRepository,
                jwt_class=TokenObtainPairSerializer,
            ).update_tokens(data=jwt_data["payloads"])

        # Asserting that the tokens were not generated
        assert JWT.objects.count() == 0

        # Assert that the refresh token was not added to the blacklist
        assert JWTBlacklist.objects.count() == 0

    def test_if_tokens_not_match_user_last_tokens(self) -> None:
        """
        This test checks if the application raises an exception when the JWT does not
        match the user.
        """

        # Creating the user data and the JWTs to be used in the test
        user, _ = self.user_factory.create_searcher_user(
            active=True, save=True, add_perm=False
        )
        jwt_data = self.jwt_factory.access_and_refresh(
            user=user,
            role="AnyUser",
            exp_access=True,
            exp_refresh=False,
            save=False,
        )

        # Other tokens are created in order to raise the exception
        _ = self.jwt_factory.access_and_refresh(
            user=user,
            role="AnyUser",
            exp_access=True,
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
        self, user_repository: Mock, jwt_repository: Mock, jwt_class: Mock
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
        get_token: Mock = jwt_class.get_token
        get_user_data.return_value = empty_queryset(model=User)

        # Creating the JWTs to be used in the test
        jwt_data = self.jwt_factory.access_and_refresh(
            user=User(),
            role="AnyUser",
            exp_access=True,
            exp_refresh=False,
            save=False,
        )

        # Instantiating the application
        with pytest.raises(ResourceNotFoundAPIError):
            _ = self.application_class(
                user_repository=user_repository,
                jwt_repository=jwt_repository,
                jwt_class=jwt_class,
            ).update_tokens(data=jwt_data["payloads"])

        # Asserting that the methods not called
        get_jwt.assert_not_called()
        add_to_blacklist.assert_not_called()
        add_to_checklist.assert_not_called()
        get_token.assert_not_called()

    def test_if_conection_db_failed(
        self, user_repository: Mock, jwt_repository: Mock, jwt_class: Mock
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
        get_token: Mock = jwt_class.get_token
        get_user_data.side_effect = DatabaseConnectionAPIError

        # Creating the JWTs to be used in the test
        jwt_data = self.jwt_factory.access_and_refresh(
            user=User(),
            role="AnyUser",
            exp_access=True,
            exp_refresh=False,
            save=False,
        )

        # Instantiating the application
        with pytest.raises(DatabaseConnectionAPIError):
            _ = self.application_class(
                user_repository=user_repository,
                jwt_class=jwt_class,
                jwt_repository=jwt_repository,
            ).update_tokens(data=jwt_data["payloads"])

        # Asserting that the methods not called
        get_jwt.assert_not_called()
        add_to_blacklist.assert_not_called()
        add_to_checklist.assert_not_called()
        get_token.assert_not_called()
