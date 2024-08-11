from apps.users.domain.constants import USER_ROLE_PERMISSIONS, UserRoles
from apps.users.domain.abstractions import (
    IUserRepository,
    IJWTRepository,
    ITokenClass,
)
from apps.users.models import User, JWT, UserManager
from apps.emails.domain.abstractions import ITokenRepository
from apps.emails.utils import TokenGenerator
from tests.utils import fake
from rest_framework_simplejwt.utils import datetime_from_epoch
from django.contrib.auth.models import Group, Permission
from django.db.models.query import QuerySet
from typing import Callable, Tuple, Dict, Any
from unittest.mock import Mock
from copy import deepcopy
import pytest


@pytest.fixture
def setup_database(db) -> None:
    """
    Set up data for the whole TestCase.
    """

    for role in [UserRoles.SEARCHER.value]:
        # Create the group and assign permissions
        group = Group.objects.create(name=role)

        for perm_codename in USER_ROLE_PERMISSIONS[role]["perm_codename_list"]:
            perm = Permission.objects.get(codename=perm_codename)
            group.permissions.add(perm)


@pytest.fixture
def create_user() -> Callable[[bool, str, bool], Tuple[User, Dict[str, Dict]]]:
    """
    A fixture to create a user in the database and return the User and the data used to
    create it.
    """

    def user(
        active: bool, role: str, add_perm: bool, **user_data
    ) -> Tuple[User, Dict[str, Dict]]:
        """
        Create a user in the database.

        #### Parameters:
        - active: A boolean that indicates if the user is active.
        - role: A string that indicates the role of the user.
        - add_perm: A boolean indicating whether the user's role permissions should be
        added to the user.
        """

        data = {
            UserRoles.SEARCHER.value: {
                "base_data": {
                    "email": user_data.get("email", None) or fake.email(),
                    "password": user_data.get("password", None)
                    or "contraseña1234",
                },
                "role_data": {
                    "name": user_data.get("name", None) or fake.name(),
                    "last_name": user_data.get("last_name", None)
                    or fake.last_name(),
                    "cc": user_data.get("cc", None)
                    or fake.random_number(digits=9),
                    "address": user_data.get("address", None) or fake.address(),
                    "phone_number": user_data.get("phone_number", None)
                    or fake.phone_number(),
                },
            },
        }
        user_data = deepcopy(data)

        user_maager: UserManager = User.objects
        user = user_maager.create_user(
            base_data=user_data[role]["base_data"],
            role_data=user_data[role]["role_data"],
            related_model_name=role,
            is_active=active,
        )

        # Add the user to the group
        if add_perm:
            group = Group.objects.get(name=role)
            user.groups.add(group)
            user.save()

        return user, data[role]

    return user


@pytest.fixture
def save_jwt_db() -> Callable[[User, Dict[str, Any]], JWT]:
    """
    A fixture to save a JSON Web Token in the database and return the JWT and the data
    used to create it.
    """

    def jwt(user: User, data: Dict) -> JWT:

        return JWT.objects.create(
            user=user,
            jti=data["payload"]["jti"],
            token=data["token"],
            expires_at=datetime_from_epoch(ts=data["payload"]["exp"]),
        )

    return jwt


@pytest.fixture
def queryset() -> Mock:
    """
    Mock the `QuerySet` class.
    """

    return Mock(spec_set=QuerySet, name="QuerySetMock")


@pytest.fixture
def user_repository() -> Mock:
    """
    Mock the `UserRepository` class.
    """

    return Mock(spec_set=IUserRepository, name="UserRepositoryMock")


@pytest.fixture
def jwt_repository() -> Mock:
    """
    Mock the `JWTRepository` class.
    """

    return Mock(spec_set=IJWTRepository, name="JWTRepositoryMock")


@pytest.fixture
def token_repository() -> Mock:
    """
    Mock the `ITokenRepository` class.
    """

    return Mock(spec_set=ITokenRepository, name="ITokenRepositoryMock")


@pytest.fixture
def jwt_class() -> Mock:
    """
    Mock the `TokenClass` class.
    """

    return Mock(spec_set=ITokenClass, name="TokenClassMock")


@pytest.fixture
def token_class() -> Mock:
    """
    Mock the `TokenGenerator` class.
    """

    return Mock(spec_set=TokenGenerator, name="TokenGeneratorMock")
