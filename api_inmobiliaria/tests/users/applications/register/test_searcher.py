from apps.users.infrastructure.db import UserRepository
from apps.users.applications import RegisterUser
from apps.users.domain.constants import USER_ROLE_PERMISSIONS, UserRoles
from apps.users.models import BaseUser, Searcher
from apps.emails.domain.constants import SubjectsMail
from apps.api_exceptions import DatabaseConnectionAPIError
from tests.factory import UserFactory
from django.test import RequestFactory
from django.core import mail
from unittest.mock import Mock
from typing import Callable
import pytest


class TestRegisterSearcherApplication:
    """
    This class encapsulates the tests for the use case or business logic
    responsible for creating a user with the "Searcher" role.
    """

    application_class = RegisterUser
    user_factory = UserFactory

    @pytest.mark.django_db
    def test_created_successfully(self, setup_database: Callable) -> None:
        """
        This test is responsible for validating the expected behavior of the
        use case when the request data is valid.
        """

        # Creating the user data to be used in the test
        _, _, data = self.user_factory.searcher_user(
            active=False, save=False, add_perm=False
        )

        # Asserting that the user does not exist in the database
        assert not BaseUser.objects.filter(email=data["email"]).exists()
        assert not Searcher.objects.filter(name=data["name"]).exists()

        # Instantiating the application and calling the method
        self.application_class(user_repository=UserRepository).searcher(
            data=data, request=RequestFactory().post("/")
        )

        # Asserting that the user was created successfully
        user = BaseUser.objects.filter(email=data["email"]).first()
        role = Searcher.objects.filter(name=data["name"]).first()
        assert user and role

        # Asserting that the user has the correct data
        assert user.email == data["email"]
        assert user.check_password(raw_password=data["password"])
        assert user.is_active == False
        assert user.is_deleted == False
        assert role.name == data["name"]
        assert role.last_name == data["last_name"]
        assert role.cc == None
        assert role.address == None
        assert role.phone_number == None
        assert role.is_phone_verified == False

        # The value of this field is changed to true since a user's permissions can
        # only be validated if this field has a value of true.
        user.is_active = True
        user.save()

        # Asserting that the user has the correct permissions
        for permission in list(
            USER_ROLE_PERMISSIONS[UserRoles.SEARCHER.value].values()
        ):
            assert user.has_perm(perm=permission)

        # Asserting that the email was sent
        assert len(mail.outbox) == 1
        assert mail.outbox[0].subject == SubjectsMail.ACCOUNT_ACTIVATION.value
        assert mail.outbox[0].to[0] == data["email"]

    def test_if_conection_db_failed(self, user_repository: Mock) -> None:
        """
        This test is responsible for validating the expected behavior of the
        use case when a DatabaseConnectionAPIError exception is raised.
        """

        # Creating the user data to be used in the test
        _, _, data = self.user_factory.searcher_user(
            active=False, save=False, add_perm=False
        )

        # Mocking the methods
        create: Mock = user_repository.create
        create.side_effect = DatabaseConnectionAPIError

        # Instantiating the application and calling the method
        with pytest.raises(DatabaseConnectionAPIError):
            self.application_class(user_repository=user_repository).searcher(
                data=data, request=RequestFactory().post("/")
            )

        # Asserting that the email was not sent
        assert len(mail.outbox) == 0
