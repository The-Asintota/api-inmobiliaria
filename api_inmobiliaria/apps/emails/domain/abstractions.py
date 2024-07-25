from apps.users.models import User
from apps.emails.domain.typing import Token
from apps.emails import models
from django.db.models import QuerySet
from typing import Protocol


class ITokenRepository(Protocol):
    """
    ITokenRepository is a protocol that defines the interface for a token repository.
    """

    @classmethod
    def create(cls, token: Token) -> None:
        """
        Inserts a new token into the database.

        #### Parameters:
        - token: Token to be inserted.

        #### Raises:
        - DatabaseConnectionError: If there is an operational error with the database.
        """

        ...

    @classmethod
    def get(cls, **filters) -> QuerySet[models.Token]:
        """
        Retrieve a token from the database based on the provided filters.

        #### Parameters:
        - filters: Keyword arguments that define the filters to apply.

        #### Raises:
        - DatabaseConnectionError: If there is an operational error with the database.
        """

        ...


class ITokenGenerator(Protocol):
    """
    ITokenGenerator is a protocol that defines the interface for a token generator.
    """

    def make_token(cls, user: User) -> str:
        """
        Generate a token for the given user and store it in the repository.

        #### Parameters:
        - user: A instance of the User model.
        """

        ...

    def check_token(cls, user: User, token: Token) -> bool:
        """
        Check that a token is correct for a given user.

        #### Parameters:
        - user: A instance of the User model.
        - token: Token to be checked.
        """

        ...
