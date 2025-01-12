from apps.users.infrastructure.repositories import UserRepository
from apps.users.applications import RegisterUser
from apps.users.constants import USER_ROLE_PERMISSIONS, UserRoles
from apps.users.models import BaseUser, RealEstateEntity
from apps.emails.constants import SubjectsMail
from apps.api_exceptions import DatabaseConnectionAPIError
from tests.factory import UserFactory
from django.test import RequestFactory
from django.core import mail
from unittest.mock import Mock
from copy import deepcopy
import pytest


class TestRegisterRealEstateEntityApplication:
    """
    This class encapsulates the tests for the use case or business logic
    responsible for creating a user with the "real estate entity" role.
    """

    application_class = RegisterUser
    user_factory = UserFactory

    @pytest.mark.django_db
    def test_created_successfully(self, setup_database) -> None:
        """
        This test is responsible for validating the expected behavior of the
        use case when the request data is valid.
        """

        # Creating the user data to be used in the test
        _, _, data = self.user_factory.real_estate_entity(save=False)
        data["phone_numbers"] = ",".join(data["phone_numbers"])

        # Asserting that the user does not exist in the database
        assert not BaseUser.objects.filter(email=data["email"]).exists()
        assert not RealEstateEntity.objects.filter(name=data["name"]).exists()

        # Instantiating the application and calling the method
        app = self.application_class(user_repository=UserRepository)
        app.real_estate_entity(
            data=deepcopy(data), request=RequestFactory().post("/")
        )

        # Asserting that the user was created successfully
        user: BaseUser = BaseUser.objects.filter(email=data["email"]).first()
        role = RealEstateEntity.objects.filter(name=data["name"]).first()
        assert user and role

        # Asserting that the user has the correct data
        assert user.email == data["email"]
        assert user.check_password(raw_password=data["password"])
        assert user.is_active == False
        assert user.is_deleted == False
        assert role.name == data["name"]
        assert role.type_entity == data["type_entity"]
        assert role.logo == data["logo"]
        assert role.description == data["description"]
        assert role.phone_numbers == data["phone_numbers"]
        assert role.department == data["department"]
        assert role.municipality == data["municipality"]
        assert role.region == data["region"]
        assert role.coordinate == data["coordinate"]
        assert role.verified == False

        for number in data["phone_numbers"].split(","):
            assert role.is_phones_verified[number] == False

        for channel in role.communication_channels.keys():
            assert role.communication_channels[channel] == False

        # The value of this field is changed to true since a user's permissions can
        # only be validated if this field has a value of true.
        user.is_active = True
        user.save()

        # Asserting that the user has the correct permissions
        user_role = UserRoles.REAL_ESTATE_ENTITY.value
        perm_model_level = USER_ROLE_PERMISSIONS[user_role]["model_level"]
        for permission in perm_model_level.values():
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
        _, _, data = self.user_factory.real_estate_entity(save=False)

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
