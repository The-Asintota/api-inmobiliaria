from apps.users.domain.constants import USER_ROLE_PERMISSIONS, UserRoles
from apps.users.domain.abstractions import (
    IUserRepository,
    IJWTRepository,
    ITokenClass,
)
from apps.emails.domain.abstractions import ITokenRepository
from apps.emails.utils import TokenGenerator
from django.contrib.auth.models import Group, Permission
from django.db.models.query import QuerySet
from unittest.mock import Mock
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
