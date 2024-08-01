from django.contrib.auth.models import Group
from apps.users.domain.abstractions import IUserRepository
from apps.users.domain.constants import UserRoles
from apps.users.signals import user_registered
from rest_framework.request import Request
from typing import Dict, Any


class SearcherUsesCases:
    """
    Uses cases for the searcher user role. It contains the business logic for the
    operations that can be performed by a user with the `searcheruser` role.
    """

    __signal = user_registered

    def __init__(self, user_repository: IUserRepository) -> None:
        self.__user_repository = user_repository

    def create_user(self, data: Dict[str, Any], request: Request) -> None:
        """
        Create a new user with the given data.

        #### Parameters:
        - data: The data to create the user with.
        - request: The request object that contains the information about the
        incoming request.
        """

        user = self.__user_repository.create(
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

        # Add the user to the group
        group = Group.objects.get(name=UserRoles.SEARCHER.value)
        user.groups.add(group)
        user.save()

        self.__signal.send(sender=__name__, user=user, request=request)
