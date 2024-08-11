from settings.environments.base import SIMPLE_JWT
from apps.users.domain.constants import (
    ACCESS_TOKEN_LIFETIME,
    REFRESH_TOKEN_LIFETIME,
    UserRoles,
)
from apps.users.domain.typing import (
    AccessToken,
    RefreshToken,
    JWTPayload,
    UserUUID,
)
from apps.users.models import User, JWT, UserManager
from apps.emails.utils import TokenGenerator
from apps.emails.models import Token
from tests.utils import fake
from rest_framework_simplejwt.utils import aware_utcnow, datetime_to_epoch
from django.contrib.auth.models import Group
from typing import Tuple, Dict, Any
from datetime import datetime
from copy import deepcopy
from jwt import encode
from uuid import uuid4


class UserFactory:
    """
    Factory in charge of creating users with false data.
    """

    model = User

    @classmethod
    def _create_user(
        cls, data: Dict[str, Any], role: str, active: bool
    ) -> User:
        """
        This method creates a user with the provided data.
        """

        user_maager: UserManager = cls.model.objects

        return user_maager.create_user(
            base_data=data["base_data"],
            role_data=data["role_data"],
            related_model_name=role,
            is_active=active,
        )

    @classmethod
    def _assign_permissions(user: User, role: str) -> None:
        """
        This method assigns the permissions of the provided role to the user.
        """

        group = Group.objects.get(name=role)
        user.groups.add(group)
        user.save()

    @classmethod
    def create_searcher_user(
        cls,
        active: bool,
        add_perm: bool,
        save: bool,
        **data: Dict[str, Any],
    ) -> Tuple[User | None, Dict[str, Dict]]:
        """
        This method creates a searcher user with the provided data.
        """

        if add_perm and not save:
            raise ValueError(
                "The user must be saved in order to assign permissions."
            )

        user = None
        user_data = {
            "base_data": {
                "email": data.get("email", None) or fake.email(),
                "password": data.get("password", None) or "contraseña1234",
            },
            "role_data": {
                "name": data.get("name", None) or fake.name(),
                "last_name": data.get("last_name", None) or fake.last_name(),
                "cc": data.get("cc", None) or fake.random_number(digits=9),
                "address": data.get("address", None) or fake.address(),
                "phone_number": data.get("phone_number", None)
                or fake.phone_number(),
            },
        }

        if save:
            user = cls._create_user(
                data=deepcopy(user_data),
                active=active,
                role=UserRoles.SEARCHER.value,
            )
        elif add_perm:
            cls._assign_permissions(user=user, role=UserRoles.SEARCHER.value)

        return user, user_data


class TokenFactory:
    """
    Factory for the token that is used in various user-related email communication,
    the token is a unique identifier that ensures the security and validity of the
    processes initiated.
    """

    def __init__(self, user: User) -> None:
        self.value = TokenGenerator().make_token(user=user)

    def save(self) -> Token:
        """
        This method saves the token in the database.
        """

        return Token.objects.create(token=self.value)

    def __str__(self) -> str:
        return self.value


class JWTFactory:
    """
    Factory for the JWT tokens.
    """

    @staticmethod
    def _get_payload(
        token_type: str, exp: datetime, user_uuid: UserUUID, role: str
    ) -> JWTPayload:
        """
        This method returns the payload for a token.

        #### Parameters:
        - token_type: The type of token to create.
        - exp: The expiration date of the token.
        - user_uuid: The UUID of the user.
        - role: The role of the user.
        """

        return {
            "token_type": token_type,
            "exp": datetime_to_epoch(exp),
            "iat": datetime_to_epoch(aware_utcnow()),
            "jti": uuid4().hex,
            "user_uuid": user_uuid,
            "role": role,
        }

    @classmethod
    def _create(
        cls,
        token_type: str,
        exp: datetime,
        user_uuid: UserUUID,
        role: str,
    ) -> Dict[str, Any]:
        """
        This method creates a token with the provided parameters, returning the token and the payload.

        #### Parameters:
        - token_type: The type of token to create.
        - exp: The expiration date of the token.
        - user_uuid: The UUID of the user.
        - role: The role of the user.
        """

        payload = cls._get_payload(
            token_type=token_type, exp=exp, user_uuid=user_uuid, role=role
        )
        token = encode(
            payload=payload,
            key=SIMPLE_JWT["SIGNING_KEY"],
            algorithm=SIMPLE_JWT["ALGORITHM"],
        )

        return {"token": token, "payload": payload}

    @classmethod
    def access(
        cls, exp: bool, user_uuid: UserUUID = None, role: str = None
    ) -> Dict[str, Any]:
        """
        Creates an access token.

        #### Parameters:
        - user_uuid: The UUID of the user.
        - role: The role of the user.
        - expired: If the token should be expired.
        """

        exp_token = (
            aware_utcnow() - ACCESS_TOKEN_LIFETIME
            if exp
            else aware_utcnow() + ACCESS_TOKEN_LIFETIME
        )

        return cls._create(
            token_type="access",
            user_uuid=user_uuid if user_uuid else uuid4().__str__(),
            role=role if role else UserRoles.SEARCHER.value,
            exp=exp_token,
        )

    @classmethod
    def refresh(
        cls, exp: bool, user_uuid: UserUUID = None, role: str = None
    ) -> Dict[str, Any]:
        """
        Creates a refresh token.

        #### Parameters:
        - user_uuid: The UUID of the user.
        - role: The role of the user.
        - expired: If the token should be expired.
        """

        exp_token = (
            aware_utcnow() - REFRESH_TOKEN_LIFETIME
            if exp
            else aware_utcnow() + REFRESH_TOKEN_LIFETIME
        )

        return cls._create(
            token_type="refresh",
            user_uuid=user_uuid if user_uuid else uuid4().__str__(),
            role=role if role else UserRoles.SEARCHER.value,
            exp=exp_token,
        )

    @classmethod
    def access_and_refresh(
        cls,
        exp_access: bool,
        exp_refresh: bool,
        user_uuid: UserUUID = None,
        role: str = None,
    ) -> Dict[str, Any]:
        """
        Creates an access and a refresh token.

        #### Parameters:
        - user_uuid: The UUID of the user.
        - role: The role of the user.
        - expired: If the token should be expired.
        """

        exp_access = (
            aware_utcnow() - ACCESS_TOKEN_LIFETIME
            if exp_access
            else aware_utcnow() + ACCESS_TOKEN_LIFETIME
        )
        exp_refresh = (
            aware_utcnow() - REFRESH_TOKEN_LIFETIME
            if exp_refresh
            else aware_utcnow() + REFRESH_TOKEN_LIFETIME
        )
        user_uuid = user_uuid if user_uuid else uuid4().__str__()
        access_data = cls._create(
            token_type="access",
            role=role if role else UserRoles.SEARCHER.value,
            user_uuid=user_uuid,
            exp=exp_access,
        )
        refresh_data = cls._create(
            token_type="refresh",
            role=role if role else UserRoles.SEARCHER.value,
            user_uuid=user_uuid,
            exp=exp_refresh,
        )

        return {
            "tokens": {
                "access": access_data["token"],
                "refresh": refresh_data["token"],
            },
            "payloads": {
                "access": access_data["payload"],
                "refresh": refresh_data["payload"],
            },
        }

    @staticmethod
    def access_invalid() -> AccessToken:

        return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNzA5MDkxZjY1MDlU3IiwidXNlcl9pZCI6IjUwNTI5MjBjLWE3ZDYtNDM4ZS1iZmQwLWVhNTUyMTM4ODM2YrCZDFxbgBxhvNBJZsLzsyCn5pabwKKKSX9VKmQ8g"

    @staticmethod
    def refresh_invalid() -> RefreshToken:

        return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlCI6MTcwNToxNzA1ODcyMjgyLCJqdGkiOiI3YWRkNjhmNTczNjY0YzNjYTNmOWUyZGRmZjZkNTI4YyIsInVzZXJfaWQiOiI1ODllMGE1NC00YmFkLTRjNTAtYTVjMi03MWIzNzY2NzdjZjULS2WTFL3YiPh3YZD-oIxXDWICs3LJ-u9BQ"
