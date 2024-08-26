from apps.users.models import BaseUser
from apps.emails.domain.typing import Token
from apps.emails import models
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
        - DatabaseConnectionAPIError: If there is an operational error with the database.
        """

        ...

    @classmethod
    def get(cls, **filters) -> models.Token:
        """
        Retrieve a token from the database based on the provided filters.

        #### Parameters:
        - filters: Keyword arguments that define the filters to apply.

        #### Raises:
        - DatabaseConnectionAPIError: If there is an operational error with the database.
        """

        ...


class ITokenGenerator(Protocol):
    """
    ITokenGenerator is a protocol that defines the interface for a token generator.
    """

    def make_token(self, base_user: BaseUser) -> str:
        """
        Generate a token for the given user.

        #### Parameters:
        - base_user: A instance of the BaseUser model.
        """

        ...

    def check_token(self, user: BaseUser, token: Token) -> bool:
        """
        Check that a token is correct for a given user.

        #### Parameters:
        - user: A instance of the BaseUser model.
        - token: Token to be checked.
        """

        ...
