from apps.users.models import User, JWT
from django.db.models import QuerySet, Model
from .typing import JWToken, AccessToken, RefreshToken
from typing import Dict, Any, Tuple, Protocol, Optional


class IUserRepository(Protocol):
    """
    IUserRepository is a protocol that defines the interface for a user repository.
    """

    @classmethod
    def create(cls, data: Dict[str, Any], role: str) -> User:
        """
        Inserts a new user into the database.

        #### Parameters:
        - data: Dictionary containing the user's data.
        - role: Role of the user.

        #### Raises:
        - DatabaseConnectionError: If there is an operational error with the database.
        """

        ...

    @classmethod
    def get(cls, **filters) -> QuerySet[User]:
        """
        Retrieves a user from the database according to the provided filters.

        #### Parameters:
        - filters: Keyword arguments that define the filters to apply.

        #### Raises:
        - DatabaseConnectionError: If there is an operational error with the database.
        """

        ...

    @classmethod
    def get_profile_data(
        cls, user: Optional[User], role: Optional[str], **filters
    ) -> QuerySet[Model]:
        """
        Retrieves the related data of a user profile from the database according to the
        provided filters.

        #### Parameters:
        - user: User instance from which to retrieve the related data.
        - role: Role of the user from which to retrieve the related data.
        - filters: Keyword arguments that define the filters to apply.

        #### Raises:
        - DatabaseConnectionError: If there is an operational error with the database.
        - ValueError: If the 'user' or 'role' parameter is not provided.
        """

        ...


class IJWTRepository(Protocol):
    """
    IJWTRepository is a protocol that defines the interface for a JWT repository.
    """

    @classmethod
    def get(cls, **filters) -> QuerySet[JWT]:
        """
        Retrieve a JWT from the database based on the provided filters and limits the
        result to the last 2 records.

        #### Parameters:
        - filters: Keyword arguments that define the filters to apply.

        #### Raises:
        - DatabaseConnectionError: If there is an operational error with the database.
        """

        ...

    @classmethod
    def add_to_checklist(cls, token: JWToken, user: User) -> None:
        """
        Associate a JSON Web Token with a user by adding it to the checklist.

        This way you can keep track of which tokens are associated with which
        users, and which tokens created are pending expiration or invalidation.

        #### Parameters:
        - token: A JWToken.
        - user: An instance of the User model.

        #### Raises:
        - DatabaseConnectionError: If there is an operational error with the database.
        """

        ...

    @classmethod
    def add_to_blacklist(cls, token: JWT) -> None:
        """
        Invalidates a JSON Web Token by adding it to the blacklist.

        Once a token is blacklisted, it can no longer be used for authentication
        purposes until it is removed from the blacklist or has expired.

        #### Parameters:
        - token: An instance of the `JWT` model.

        #### Raises:
        - DatabaseConnectionError: If there is an operational error with the database.
        """

        ...


class ITokenClass(Protocol):
    """
    Interface that defines the methods that a class must implement to be used as a
    JWT class.
    """

    @classmethod
    def get_token(cls, user: User) -> Tuple[AccessToken, RefreshToken]:
        """
        Generates the JSON WEB Tokens for the user and saves them to the database.

        #### Parameters:
        - user: An instance of the User model for which to generate the tokens.
        """

        ...
