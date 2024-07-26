from enum import Enum
from datetime import timedelta


ACCESS_TOKEN_LIFETIME = timedelta(minutes=120)
REFRESH_TOKEN_LIFETIME = timedelta(days=1)


class UserRoles(Enum):
    """
    This enum represents the roles that a user can have.
    """

    SEARCHER = "searcher"


USER_ROLE_PERMISSIONS = {
    UserRoles.SEARCHER.value: [
        f"change_{UserRoles.SEARCHER.value}",
        f"delete_{UserRoles.SEARCHER.value}",
        f"view_{UserRoles.SEARCHER.value}",
        "add_jwt",
    ],
}


class UserProperties(Enum):
    """
    Define the data properties of a user.
    """

    EMAIL_MAX_LENGTH = 40
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_MAX_LENGTH = 40


class SearcherProperties(Enum):
    """
    Define the data properties of a searcher user.
    """

    NAME_MAX_LENGTH = 40
    LAST_NAME_MAX_LENGTH = 40
    CC_MIN_LENGTH = 6
    CC_MAX_LENGTH = 10
    ADDRESS_MAX_LENGTH = 90
    PHONE_NUMBER_MAX_LENGTH = 25
