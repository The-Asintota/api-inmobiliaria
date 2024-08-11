from apps.users.infrastructure.serializers import TokenObtainPairSerializer
from apps.users.infrastructure.db import JWTRepository, UserRepository
from apps.users.applications import JWTUsesCases
from apps.users.domain.constants import UserRoles
from apps.users.models import User, JWT, JWTBlacklist
from apps.api_exceptions import (
    DatabaseConnectionAPIError,
    ResourceNotFoundAPIError,
    JWTAPIError,
)
from apps.utils import decode_jwt
from tests.factory import JWTFactory
from tests.utils import empty_queryset
from unittest.mock import Mock
from typing import Callable, Tuple, Dict, Any
import pytest


class TestApplication:
    """
    This class encapsulates all the tests of the JWT use case responsible for updating
    the tokens of a user.
    """

    application_class = JWTUsesCases

    @pytest.mark.django_db
    def test_updated_tokens(
        self,
        create_user: Callable[[bool, str, bool], Tuple[User, Dict[str, Dict]]],
        save_jwt_db: Callable[[User, Dict[str, Any]], JWT],
    ) -> None:
        """
        This test case is responsible for testing the successful update of the tokens
        of a user.
        """

        # Creating a user
        user, _ = create_user(
            active=True, role=UserRoles.SEARCHER.value, add_perm=False
        )

        # Creating the token
        refresh_data = JWTFactory.refresh(
            user_uuid=user.uuid.__str__(), exp=False
        )
        access_data = JWTFactory.access(user_uuid=user.uuid.__str__(), exp=True)
        _ = save_jwt_db(user=user, data=access_data)
        _ = save_jwt_db(user=user, data=refresh_data)

        # Instantiating the application
        tokens = self.application_class(
            user_repository=UserRepository,
            jwt_repository=JWTRepository,
            jwt_class=TokenObtainPairSerializer,
        ).update_tokens(
            data={
                "refresh": refresh_data["payload"],
                "access": access_data["payload"],
            }
        )

        # Asserting that the tokens were generated
        access = tokens.get("access", False)
        refresh = tokens.get("refresh", False)

        assert access
        assert refresh

        # Assert that the refresh token was added to the blacklist
        assert JWTBlacklist.objects.filter(
            token__jti=refresh_data["payload"]["jti"]
        ).first()
        assert not JWTBlacklist.objects.filter(
            token__jti=access_data["payload"]["jti"]
        ).first()

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
    def test_if_jwt_not_found(
        self,
        create_user: Callable[[bool, str, bool], Tuple[User, Dict[str, Dict]]],
    ) -> None:
        """
        This test checks if the application raises an exception when the JWT is not
        found.
        """

        # Creating a user
        user, _ = create_user(
            active=True, role=UserRoles.SEARCHER.value, add_perm=False
        )

        # Creating the token
        refresh_data = JWTFactory.refresh(
            user_uuid=user.uuid.__str__(), exp=False
        )
        access_data = JWTFactory.access(user_uuid=user.uuid.__str__(), exp=True)

        # Instantiating the application
        with pytest.raises(ResourceNotFoundAPIError):
            _ = self.application_class(
                user_repository=UserRepository,
                jwt_repository=JWTRepository,
                jwt_class=TokenObtainPairSerializer,
            ).update_tokens(
                data={
                    "refresh": refresh_data["payload"],
                    "access": access_data["payload"],
                }
            )

        # Asserting that the tokens were not generated
        assert JWT.objects.count() == 0

        # Assert that the refresh token was not added to the blacklist
        assert JWTBlacklist.objects.count() == 0

    @pytest.mark.django_db
    def test_if_jwt_not_match_user(
        self,
        create_user: Callable[[bool, str, bool], Tuple[User, Dict[str, Dict]]],
        save_jwt_db: Callable[[User, Dict[str, Any]], JWT],
    ) -> None:
        """
        This test checks if the application raises an exception when the JWT does not
        match the user.
        """

        # Creating a user
        user, _ = create_user(
            active=True, role=UserRoles.SEARCHER.value, add_perm=False
        )

        # Creating the token
        refresh_data = JWTFactory.refresh(
            user_uuid=user.uuid.__str__(), exp=False
        )
        access_data = JWTFactory.access(user_uuid=user.uuid.__str__(), exp=True)
        _ = save_jwt_db(user=user, data=access_data)
        _ = save_jwt_db(user=user, data=refresh_data)

        # Instantiating the application
        with pytest.raises(JWTAPIError):
            _ = self.application_class(
                user_repository=UserRepository,
                jwt_repository=JWTRepository,
                jwt_class=TokenObtainPairSerializer,
            ).update_tokens(
                data={
                    "refresh": JWTFactory.refresh(
                        user_uuid=user.uuid.__str__(), exp=False
                    ).get("payload"),
                    "access": JWTFactory.access(
                        user_uuid=user.uuid.__str__(), exp=True
                    ).get("payload"),
                }
            )

        # Asserting that the tokens were not generated
        assert JWT.objects.count() <= 2

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

        # Setting the return values
        get_user_data.return_value = empty_queryset(model=User)

        # Instantiating the application
        with pytest.raises(ResourceNotFoundAPIError):
            _ = self.application_class(
                user_repository=user_repository,
                jwt_repository=jwt_repository,
                jwt_class=jwt_class,
            ).update_tokens(
                data={
                    "refresh": JWTFactory.refresh(exp=False).get("payload"),
                    "access": JWTFactory.access(exp=True).get("payload"),
                }
            )

        # Asserting that the methods not called
        get_jwt.assert_not_called()
        add_to_blacklist.assert_not_called()
        add_to_checklist.assert_not_called()
        get_token.assert_not_called()

    def test_exception_raised_db(
        self, user_repository: Mock, jwt_repository: Mock, jwt_class: Mock
    ) -> None:
        """
        This test checks if the application raises an exception when a database error
        occurs.
        """

        # Mocking the methods
        get_user_data: Mock = user_repository.get_user_data
        get_jwt: Mock = jwt_repository.get
        add_to_blacklist: Mock = jwt_repository.add_to_blacklist
        add_to_checklist: Mock = jwt_repository.add_to_checklist
        get_token: Mock = jwt_class.get_token

        # Setting the return values
        get_user_data.side_effect = DatabaseConnectionAPIError

        # Instantiating the application
        with pytest.raises(DatabaseConnectionAPIError):
            _ = self.application_class(
                user_repository=user_repository,
                jwt_class=jwt_class,
                jwt_repository=jwt_repository,
            ).update_tokens(
                data={
                    "refresh": JWTFactory.refresh(exp=False).get("payload"),
                    "access": JWTFactory.access(exp=True).get("payload"),
                }
            )

        # Asserting that the methods not called
        get_jwt.assert_not_called()
        add_to_blacklist.assert_not_called()
        add_to_checklist.assert_not_called()
        get_token.assert_not_called()
