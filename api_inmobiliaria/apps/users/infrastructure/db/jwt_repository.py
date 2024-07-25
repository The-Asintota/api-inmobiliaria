from apps.users.domain.typing import JWToken, JWTPayload
from apps.users.models import User, JWT, JWTBlacklist
from apps.exceptions import DatabaseConnectionError
from rest_framework_simplejwt.utils import datetime_from_epoch
from django.db.models import QuerySet
from django.db import OperationalError


class JWTRepository:
    """
    JWTRepository is a class that provides an abstraction of the database operations
    or queries related to a JSON Web Token.
    """

    jwt_model = JWT
    blacklist_model = JWTBlacklist

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

        try:
            tokens = (
                cls.jwt_model.objects.select_related("user")
                .defer("date_joined")
                .filter(**filters)
                .order_by("-date_joined")[:2]
            )
        except OperationalError:
            # In the future, a retry system will be implemented when the database is
            # suddenly unavailable.
            raise DatabaseConnectionError()

        return tokens

    @classmethod
    def add_to_checklist(
        cls, token: JWToken, payload: JWTPayload, user: User
    ) -> None:
        """
        Associate a JSON Web Token with a user by adding it to the checklist.

        This way you can keep track of which tokens are associated with which
        users, and which tokens created are pending expiration or invalidation.

        #### Parameters:
        - token: A JWToken.
        - payload: The payload of the token.
        - user: An instance of the User model.

        #### Raises:
        - DatabaseConnectionError: If there is an operational error with the database.
        """

        try:
            cls.jwt_model.objects.create(
                jti=payload["jti"],
                token=token,
                user=user,
                expires_at=datetime_from_epoch(ts=payload["exp"]),
            )
        except OperationalError:
            # In the future, a retry system will be implemented when the database is
            # suddenly unavailable.
            raise DatabaseConnectionError()

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

        try:
            cls.blacklist_model.objects.create(token=token)
        except OperationalError:
            # In the future, a retry system will be implemented when the database is
            # suddenly unavailable.
            raise DatabaseConnectionError()
