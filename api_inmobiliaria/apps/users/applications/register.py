from apps.users.domain.abstractions import IUserRepository
from apps.users.domain.constants import UserRoles
from apps.users.models import BaseUser
from apps.users.signals import account_activation_mail
from apps.api_exceptions import DatabaseConnectionAPIError
from django.contrib.auth.models import Group
from django.db import OperationalError
from rest_framework.request import Request
from typing import Dict, Any


class RegisterUser:
    """
    Uses cases for the user registration process.
    """

    def __init__(self, user_repository: IUserRepository) -> None:
        self._user_repository = user_repository

    def _assign_permissions(self, base_user: BaseUser, user_role: str) -> None:
        """
        This method assigns the permissions of the provided role to the user.

        #### Parameters:
        - base_user: An instance of the BaseUser model.
        - user_role: The role of the user.

        #### Raises:
        - DatabaseConnectionAPIError: If there is an operational error with the database.
        """

        try:
            group = Group.objects.get(name=user_role)
        except OperationalError:
            raise DatabaseConnectionAPIError()

        base_user.groups.add(group)
        base_user.save()

    def searcher(self, data: Dict[str, Any], request: Request) -> None:
        """
        Create a new searcher user with the given data.

        #### Parameters:
        - data: The data to create the user with.
        - request: The request object that contains the information about the
        incoming request.
        """

        base_user = self._user_repository.create(
            user_role=UserRoles.SEARCHER.value,
            data={
                "base_data": {
                    "email": data["email"],
                    "password": data["password"],
                },
                "role_data": {
                    "name": data["name"],
                    "last_name": data["last_name"],
                },
            },
            active=False,
        )

        self._assign_permissions(
            base_user=base_user, user_role=UserRoles.SEARCHER.value
        )
        account_activation_mail.send(
            sender=__name__, base_user=base_user, request=request
        )
