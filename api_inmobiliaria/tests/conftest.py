from apps.users.domain.constants import USER_ROLE_PERMISSIONS, UserRoles
from apps.users.domain.abstractions import (
    IUserRepository,
    IJWTRepository,
    ITokenClass,
)
from apps.users.models import User, JWT, UserManager
from apps.emails.utils import TokenGenerator
from rest_framework_simplejwt.utils import datetime_from_epoch
from django.contrib.auth.models import Group, Permission
from django.db.models.query import QuerySet
from typing import Callable, Tuple, Dict
from unittest.mock import Mock
import pytest


@pytest.fixture
def setup_database(db) -> None:
    """
    Set up data for the whole TestCase.
    """

    # Create the group and assign permissions
    group = Group.objects.create(name=UserRoles.SEARCHER.value)

    for perm_codename in USER_ROLE_PERMISSIONS[UserRoles.SEARCHER.value][
        "perm_codename_list"
    ]:
        perm = Permission.objects.get(codename=perm_codename)
        group.permissions.add(perm)


@pytest.fixture
def save_user_db() -> Callable[[bool, str], Tuple[User, Dict]]:
    """
    A fixture to save a user in the database and return the User and the data used to
    create it.
    """

    def user(active: bool, role: str) -> Tuple[User, Dict]:
        data = {
            "base_data": {
                "email": "user1@email.com",
                "password": "contraseña1234",
            },
            "profile_data": {
                "full_name": "Nombre Apellido",
                "address": "Residencia 1",
                "phone_number": "+57 3123574898",
            },
        }
        email = data["base_data"]["email"]
        password = data["base_data"]["password"]

        user_maager: UserManager = User.objects
        user = user_maager.create_user(
            base_data=data["base_data"],
            profile_data=data["profile_data"],
            related_model_name=role,
        )
        user.is_active = active
        user.save()

        return user, {"email": email, "password": password}

    return user


@pytest.fixture
def save_jwt_db() -> Callable[[User, Dict], JWT]:
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
def jwt_class() -> Mock:
    """
    Mock the `TokenClass` class.
    """

    return Mock(spec_set=ITokenClass, name="TokenClassMock")


@pytest.fixture
def token_generator() -> Mock:
    """
    Mock the `TokenGenerator` class.
    """

    return Mock(spec_set=TokenGenerator, name="TokenGeneratorMock")
