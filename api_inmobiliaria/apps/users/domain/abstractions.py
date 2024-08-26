from apps.users.models import BaseUser
from django.db.models import Model
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from .typing import JSONWebToken, JWTPayload
from typing import Dict, Any, Protocol


class IUserRepository(Protocol):
    """
    IUserRepository is a protocol that defines the interface for a user repository.
    """

    @classmethod
    def create(
        cls, data: Dict[str, Any], user_role: str, active: bool
    ) -> BaseUser:
        """
        Inserts a new user into the database.

        #### Parameters:
        - data: Dictionary containing the user's data.
        - user_role: Role of the user.
        - active: Boolean that indicates if the user is active or not.

        #### Raises:
        - DatabaseConnectionAPIError: If there is an operational error with the
        database.
        """

        ...

    @classmethod
    def get_base_data(cls, **filters) -> BaseUser | None:
        """
        Retrieves a user base data from the database based on the provided filters.

        #### Parameters:
        - filters: Keyword arguments that define the filters to apply.

        #### Raises:
        - DatabaseConnectionAPIError: If there is an operational error with the
        database.
        """

        ...

    @classmethod
    def get_role_data(cls, base_user: BaseUser) -> Model:
        """
        Retrieves the role data of a user.

        #### Parameters:
        - base_user: An instance of the BaseUser model.

        #### Raises:
        - DatabaseConnectionAPIError: If there is an operational error with the
        database.
        """

        ...

    @classmethod
    def role_data_exists(cls, user_role: str, **filters) -> bool:
        """
        Checks if a user exists in the database.

        #### Parameters:
        - user_role: Role of the user.
        - filters: Keyword arguments that define the filters to apply.

        #### Raises:
        - DatabaseConnectionAPIError: If there is an operational error with the
        database.
        """

        ...

    @classmethod
    def base_data_exists(cls, **filters) -> bool:
        """
        Checks if a user base data exists in the database.

        #### Parameters:
        - filters: Keyword arguments that define the filters to apply.

        #### Raises:
        - DatabaseConnectionAPIError: If there is an operational error with the
        database.
        """

        ...

    @classmethod
    def update_role_data(
        cls,
        base_user: BaseUser,
        data: Dict[str, Any],
    ) -> Model:
        """
        Updates the role data for a user.

        #### Parameters:
        - base_user: An instance of the BaseUser model.
        - data: Dictionary containing the data to update.

        #### Raises:
        - DatabaseConnectionAPIError: If there is an operational error with the
        database.
        """

        ...


class IJWTRepository(Protocol):
    """
    IJWTRepository is a protocol that defines the interface for a JWT repository.
    """

    @classmethod
    def get(cls, **filters) -> OutstandingToken:
        """
        Retrieve a JWT from the database based on the provided filters and limits the
        result to the last 2 records.

        #### Parameters:
        - filters: Keyword arguments that define the filters to apply.

        #### Raises:
        - DatabaseConnectionAPIError: If there is an operational error with the database.
        """

        ...

    @classmethod
    def add_checklist(
        cls, token: JSONWebToken, payload: JWTPayload, user: BaseUser
    ) -> None:
        """
        Associate a JSON Web Token with a user by adding it to the checklist.

        This way you can keep track of which tokens are associated with which
        users, and which tokens created are pending expiration or invalidation.

        #### Parameters:
        - token: A JSONWebToken.
        - payload: The payload of the token.
        - user: An instance of the BaseUser model.

        #### Raises:
        - DatabaseConnectionAPIError: If there is an operational error with the database.
        """

        ...

    @classmethod
    def add_blacklist(cls, token: OutstandingToken) -> None:
        """
        Invalidates a JSON Web Token by adding it to the blacklist.

        Once a token is blacklisted, it can no longer be used for authentication
        purposes until it is removed from the blacklist or has expired.

        #### Parameters:
        - token: An instance of the `OutstandingToken` model.

        #### Raises:
        - DatabaseConnectionAPIError: If there is an operational error with the database.
        """

        ...

    @classmethod
    def exists_in_blacklist(cls, jti: str) -> bool:
        """
        Check if a token exists in the blacklist.

        #### Parameters:
        - jti: The JTI of the token.

        #### Raises:
        - DatabaseConnectionAPIError: If there is an operational error with the database.
        """

        ...
