from apps.emails.domain.typing import Token
from apps.emails import models
from apps.api_exceptions import DatabaseConnectionAPIError
from django.db import OperationalError
from django.db.models import QuerySet


class TokenRepository:
    """
    TokenRepository is a class that provides an abstraction of the database operations
    or queries related to a token.
    """

    __model = models.Token

    @classmethod
    def create(cls, token: Token) -> None:
        """
        Inserts a new token into the database.

        #### Parameters:
        - token: Token to be inserted.

        #### Raises:
        - DatabaseConnectionAPIError: If there is an operational error with the database.
        """

        try:
            cls.__model.objects.create(token=token)
        except OperationalError:
            raise DatabaseConnectionAPIError()

    @classmethod
    def get(cls, **filters) -> QuerySet[models.Token]:
        """
        Retrieve a token from the database based on the provided filters.

        #### Parameters:
        - filters: Keyword arguments that define the filters to apply.

        #### Raises:
        - DatabaseConnectionAPIError: If there is an operational error with the database.
        """

        try:
            tokens = cls.__model.objects.defer("date_joined").filter(**filters)
        except OperationalError:
            raise DatabaseConnectionAPIError()

        return tokens
