from apps.users.infrastructure.db import UserRepository
from apps.users.models import BaseUser
from rest_framework.request import Request
from django.contrib.auth.backends import ModelBackend


class EmailBackend(ModelBackend):
    """
    A `custom authentication backend` that authenticates users based on their email
    and password.
    """

    _user_repository = UserRepository

    def authenticate(
        self, request: Request, email: str, password: str
    ) -> BaseUser | None:
        """
        Authenticate a user with the given email and password.
        """

        user = self._user_repository.get_base_data(email=email)

        if not user:
            return None

        return user if user.check_password(raw_password=password) else None
