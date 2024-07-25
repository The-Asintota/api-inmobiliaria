from apps.users.infrastructure.db import JWTRepository, UserRepository
from apps.users.applications import JWTUsesCases
from apps.users.models import UserWTBlacklist, UserRoles
from apps.exceptions import (
    DatabaseConnectionError,
    ResourceNotFoundError,
    JWTError,
)
from tests.users.factory import JWTFactory
from tests.utils import empty_queryset
from unittest.mock import Mock
import pytest


class TestApplication:
    """
    A test class for the `JWTUsesCases` application. This class contains test methods
    to verify the behavior of use cases for logout user.
    """

    application_class = JWTUsesCases

    @pytest.mark.django_db
    def test_logout_user(self, save_user_db, save_jwt_db) -> None:
        # Creating a user
        user, _ = save_user_db(active=True, role=UserRoles.SEARCHER.value)

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
        # Creating the token
        refresh_data = JWTFactory.refresh(exp=False)
        access_data = JWTFactory.access(exp=False)

        # Mocking the methods
        get_user: Mock = user_repository.get
        first: Mock = get_user.first
        get_jwt: Mock = jwt_repository.get
        add_to_blacklist: Mock = jwt_repository.add_to_blacklist
        add_to_checklist: Mock = jwt_repository.add_to_checklist

        # Setting the return values
        get_jwt.return_value = empty_queryset(model=JWT)
        first.return_value = User

        # Instantiating the application
        with pytest.raises(ResourceNotFoundError):
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
    def test_if_jwt_not_match_user(self, save_user_db, save_jwt_db) -> None:
        # Creating a user
        user, _ = save_user_db(active=True, role=UserRoles.SEARCHER.value)

        # Creating the token
        refresh_data = JWTFactory.refresh(
            user_uuid=user.uuid.__str__(), exp=False
        )
        access_data = JWTFactory.access(user_uuid=user.uuid.__str__(), exp=True)
        _ = save_jwt_db(user=user, data=access_data)
        _ = save_jwt_db(user=user, data=refresh_data)

        # Instantiating the application
        with pytest.raises(JWTError):
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
        # Mocking the methods
        get_user: Mock = user_repository.get
        get_jwt: Mock = jwt_repository.get
        add_to_blacklist: Mock = jwt_repository.add_to_blacklist
        add_to_checklist: Mock = jwt_repository.add_to_checklist

        # Setting the return values
        get_user.return_value = empty_queryset(model=User)

        # Instantiating the application
        with pytest.raises(ResourceNotFoundError):
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
        # Mocking the methods
        get_user: Mock = user_repository.get
        get_jwt: Mock = jwt_repository.get
        add_to_blacklist: Mock = jwt_repository.add_to_blacklist
        add_to_checklist: Mock = jwt_repository.add_to_checklist

        # Setting the return values
        get_user.side_effect = DatabaseConnectionError

        # Instantiating the application
        with pytest.raises(DatabaseConnectionError):
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
