from apps.users.infrastructure.db import JWTRepository, UserRepository
from apps.users.applications import JWTUsesCases
from apps.users.domain.constants import UserRoles
from apps.users.models import User, JWTBlacklist, JWT
from apps.api_exceptions import (
    DatabaseConnectionAPIError,
    ResourceNotFoundAPIError,
    JWTAPIError,
)
from tests.factory import JWTFactory
from tests.utils import empty_queryset
from unittest.mock import Mock
from typing import Callable, Tuple, Dict, Any
import pytest


class TestApplication:
    """
    This class encapsulates all the tests of the JWT use case responsible for logout
    of a user.
    """

    application_class = JWTUsesCases

    @pytest.mark.django_db
    def test_logout_user(
        self,
        create_user: Callable[[bool, str, bool], Tuple[User, Dict[str, Dict]]],
        save_jwt_db: Callable[[User, Dict[str, Any]], JWT],
    ) -> None:
        """
        This test checks if the user is logged out correctly, adding the refresh token
        to the blacklist.
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

        # Asserting the tokens are not in the blacklist
        assert JWTBlacklist.objects.count() == 0

        # Instantiating the application
        self.application_class(
            user_repository=UserRepository,
            jwt_repository=JWTRepository,
        ).logout_user(
            data={
                "refresh": refresh_data["payload"],
                "access": access_data["payload"],
            }
        )

        # Assert that the refresh token was added to the blacklist
        assert JWTBlacklist.objects.filter(
            token__jti=refresh_data["payload"]["jti"]
        ).first()
        assert not JWTBlacklist.objects.filter(
            token__jti=access_data["payload"]["jti"]
        ).first()

    def test_if_jwt_not_found(
        self, user_repository: Mock, jwt_repository: Mock
    ) -> None:
        """
        This test checks if the application raises an exception when the JWT is not found.
        """

        # Creating the token
        refresh_data = JWTFactory.refresh(exp=False)
        access_data = JWTFactory.access(exp=False)

        # Mocking the methods
        get_user_data: Mock = user_repository.get_user_data
        first: Mock = get_user_data.first
        get_jwt: Mock = jwt_repository.get
        add_to_blacklist: Mock = jwt_repository.add_to_blacklist
        add_to_checklist: Mock = jwt_repository.add_to_checklist

        # Setting the return values
        get_jwt.return_value = empty_queryset(model=JWT)
        first.return_value = User

        # Instantiating the application
        with pytest.raises(ResourceNotFoundAPIError):
            self.application_class(
                user_repository=user_repository,
                jwt_repository=jwt_repository,
            ).logout_user(
                data={
                    "refresh": refresh_data["payload"],
                    "access": access_data["payload"],
                }
            )

        # Asserting that the methods not called
        add_to_blacklist.assert_not_called()
        add_to_checklist.assert_not_called()

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
            self.application_class(
                user_repository=UserRepository,
                jwt_repository=JWTRepository,
            ).logout_user(
                data={
                    "refresh": JWTFactory.refresh(
                        user_uuid=user.uuid.__str__(), exp=False
                    ).get("payload"),
                    "access": JWTFactory.access(
                        user_uuid=user.uuid.__str__(), exp=False
                    ).get("payload"),
                }
            )

        # Asserting that the tokens were not generated
        assert JWT.objects.count() <= 2

        # Assert that the refresh token was not added to the blacklist
        assert JWTBlacklist.objects.count() == 0

    def test_if_user_not_found(
        self,
        user_repository: Mock,
        jwt_repository: Mock,
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

        # Setting the return values
        get_user_data.return_value = empty_queryset(model=User)

        # Instantiating the application
        with pytest.raises(ResourceNotFoundAPIError):
            self.application_class(
                user_repository=user_repository,
                jwt_repository=jwt_repository,
            ).logout_user(
                data={
                    "refresh": JWTFactory.refresh(exp=False).get("payload"),
                    "access": JWTFactory.access(exp=False).get("payload"),
                }
            )

        # Asserting that the methods not called
        get_jwt.assert_not_called()
        add_to_blacklist.assert_not_called()
        add_to_checklist.assert_not_called()

    def test_exception_raised_db(
        self, user_repository: Mock, jwt_repository: Mock
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

        # Setting the return values
        get_user_data.side_effect = DatabaseConnectionAPIError

        # Instantiating the application
        with pytest.raises(DatabaseConnectionAPIError):
            self.application_class(
                user_repository=user_repository,
                jwt_repository=jwt_repository,
            ).logout_user(
                data={
                    "refresh": JWTFactory.refresh(exp=False).get("payload"),
                    "access": JWTFactory.access(exp=False).get("payload"),
                }
            )

        # Asserting that the methods not called
        get_jwt.assert_not_called()
        add_to_blacklist.assert_not_called()
        add_to_checklist.assert_not_called()
