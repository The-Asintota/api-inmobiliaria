from django.contrib.auth.models import Group
from apps.users.domain.abstractions import IUserRepository
from apps.users.domain.constants import UserRoles
from apps.users.models import User
from apps.users.signals import account_activation_mail
from rest_framework.request import Request
from typing import Dict, Any


class RegisterUser:
    """
    Uses cases for the user registration process.
    """

    def __init__(self, user_repository: IUserRepository) -> None:
        self._user_repository = user_repository

    def _assign_permissions(self, user: User, role: str) -> None:
        """
        This method assigns the permissions of the provided role to the user.
        """

        group = Group.objects.get(name=UserRoles.SEARCHER.value)
        user.groups.add(group)
        user.save()

    def searcher(self, data: Dict[str, Any], request: Request) -> None:
        """
        Create a new searcher user with the given data.

        #### Parameters:
        - data: The data to create the user with.
        - request: The request object that contains the information about the
        incoming request.
        """

        user = self._user_repository.create(
            role=UserRoles.SEARCHER.value,
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
            is_active=False,
        )

        self._assign_permissions(user=user, role=UserRoles.SEARCHER.value)
        account_activation_mail.send(
            sender=__name__, user=user, request=request
        )
