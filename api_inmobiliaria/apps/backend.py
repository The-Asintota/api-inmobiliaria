from apps.users.infrastructure.db import UserRepository
from apps.users.models import User
from rest_framework.request import Request
from django.contrib.auth.backends import ModelBackend


class EmailBackend(ModelBackend):
    """
    A `custom authentication backend` that authenticates users based on their email
    and password.
    """

    def authenticate(
        self, request: Request, email: str, password: str
    ) -> User | None:
        """
        Authenticate a user with the given email and password.
        """

        user = UserRepository.get_user_data(email=email).first()

        if not user:
            return None

        return user if user.check_password(raw_password=password) else None
