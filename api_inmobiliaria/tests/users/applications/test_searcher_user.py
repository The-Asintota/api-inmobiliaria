from apps.users.infrastructure.db import UserRepository
from apps.users.applications import SearcherUsesCases
from apps.users.domain.constants import USER_ROLE_PERMISSIONS, UserRoles
from apps.users.models import User, Searcher
from apps.emails.domain.constants import SubjectsMail
from apps.exceptions import DatabaseConnectionError
from django.contrib.auth.models import Permission
from django.test import RequestFactory
from django.core import mail
from unittest.mock import Mock
from typing import Callable
import pytest


class TestCreateSearcherUser:
    """
    This class encapsulates the tests for the use case or business logic
    responsible for creating a user with the "Searcher" role.
    """

    application_class = SearcherUsesCases

    @pytest.mark.django_db
    def test_created_successfully(self, setup_database: Callable) -> None:
        """
        This test is responsible for validating the expected behavior of the
        `create_user` method when the user data is valid. This method is
        responsible for creating a user with the "Searcher" role.
        """

        data = {
            "name": "Nombre del usuario",
            "last_name": "Apellido del usuario",
            "email": "user1@email.com",
            "password": "contraseña1234",
            "confirm_password": "contraseña1234",
        }

        # Asserting that the user does not exist in the database
        assert not User.objects.filter(email=data["email"]).exists()
        assert not Searcher.objects.filter(name=data["name"]).exists()

        self.application_class(user_repository=UserRepository).create_user(
            data=data.copy(),
            request=RequestFactory().post("/"),
        )

        # Asserting that the user was created successfully
        user = User.objects.filter(email=data["email"]).first()
        assert user
        assert Searcher.objects.filter(name=data["name"]).exists()

        # The value of this field is changed to true since a user's permissions can
        # only be validated if this field has a value of true.
        user.is_active = True
        user.save()

        # Asserting that the user has the correct permissions
        for codename in USER_ROLE_PERMISSIONS[UserRoles.SEARCHER.value][
            "perm_codename_list"
        ]:
            perm = Permission.objects.get(codename=codename)
            assert user.has_perm(
                perm=f"{perm.content_type.app_label}.{perm.codename}"
            )

        # Asserting that the email was sent
        assert len(mail.outbox) == 1
        assert mail.outbox[0].subject == SubjectsMail.ACCOUNT_ACTIVATION.value
        assert mail.outbox[0].to[0] == data["email"]

    def test_exception_raised_db(self, user_repository: Mock) -> None:
        """
        This test is responsible for validating the expected behavior of the
        `create_user` method when a DatabaseConnectionError exception is raised
        during the user creation process.
        """

        # Mocking the methods of the UserRepository class
        # To control the behavior of serializer validations that use these methods
        # We make it return a DatabaseConnectionError exception
        create: Mock = user_repository.create
        create.side_effect = DatabaseConnectionError

        # Instantiating the application and calling the method
        with pytest.raises(DatabaseConnectionError):
            self.application_class(user_repository=user_repository).create_user(
                data={
                    "name": "Nombre del usuario",
                    "last_name": "Apellido del usuario",
                    "email": "user1@email.com",
                    "password": "contraseña1234",
                    "confirm_password": "contraseña1234",
                },
                request=RequestFactory().post("/"),
            )

        # Asserting that the email was not sent
        assert len(mail.outbox) == 0
