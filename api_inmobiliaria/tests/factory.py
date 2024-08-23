from settings.environments.base import SIMPLE_JWT
from apps.users.domain.constants import (
    ACCESS_TOKEN_LIFETIME,
    REFRESH_TOKEN_LIFETIME,
    UserRoles,
)
from apps.users.domain.typing import (
    AccessToken,
    RefreshToken,
    JSONWebToken,
    JWTPayload,
    UserUUID,
)
from apps.users.models import User
from apps.emails.models import Token
from apps.utils.generators import TokenGenerator
from tests.utils import fake
from rest_framework_simplejwt.token_blacklist.models import (
    OutstandingToken,
    BlacklistedToken,
)
from rest_framework_simplejwt.utils import (
    aware_utcnow,
    datetime_to_epoch,
    datetime_from_epoch,
)
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Group
from django.db.models import Model
from django.utils import timezone
from typing import Optional, Tuple, Dict, Any
from datetime import datetime
from jwt import encode
from uuid import uuid4


class UserFactory:
    """
    Factory in charge of creating users with false data.
    """

    model = User

    @classmethod
    def _create_user(
        cls, data: Dict[str, Dict[str, Any]], role_user: str, active: bool
    ) -> Tuple[User, Model]:
        """
        This method creates a user with the provided data in the database.

        #### Parameters:
        - data: The data to create the user.
        - role_user: The role of the user.
        - active: If the user should be active.
        """

        related_model = ContentType.objects.get(model=role_user).model_class()
        role_user_instance = related_model.objects.create(**data["role_data"])

        password = data["base_data"].pop("password")
        base_user_instance = cls.model.objects.create(
            content_object=role_user_instance,
            is_active=active,
            **data["base_data"],
        )
        base_user_instance.set_password(password)
        base_user_instance.save()

        return base_user_instance, role_user_instance

    @classmethod
    def _assign_permissions(cls, user: User, role_user: str) -> None:
        """
        This method assigns the permissions of the provided role to the user.

        #### Parameters:
        - user: An instance of the User model.
        - role_user: The role of the user.
        """

        group = Group.objects.get(name=role_user)
        user.groups.add(group)
        user.save()

    @classmethod
    def _get_data(
        cls, role_user: str, **data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        This method returns the data for the user creation.

        #### Parameters:
        - role_user: The role of the user.
        - data: The data to create the user.
        """

        data = {
            UserRoles.SEARCHER.value: {
                "email": data.get("email", None) or fake.email(),
                "password": "contraseña1234",
                "name": "Nombre del ususario",
                "last_name": "Apellido del usuario",
                "cc": data.get("cc", None) or str(fake.random_number(digits=9)),
                "address": data.get("address", None) or fake.address(),
                "phone_number": data.get("phone_number", None)
                or fake.phone_number(),
            }
        }

        return data[role_user]

    @classmethod
    def user(
        cls,
        role_user: str,
        active: bool,
        add_perm: bool,
        save: bool,
        **data: Dict[str, Any],
    ) -> Tuple[User, Model, Dict[str, Any]]:
        """
        This method creates a user with the provided data.

        #### Parameters:
        - role_user: The role of the user.
        - save: If the user should be saved in the database.
        - add_perm: If the user should have the permissions assigned.
        - active: If the user should be active.
        - data: The data to create the user.

        #### Returns:
        - A tuple of an instance of the User models and the model of the indicated
        role or "None" and the user data.
        """

        method_map = {
            UserRoles.SEARCHER.value: cls.searcher_user,
        }
        user_data = cls._get_data(role_user=role_user, **data)

        return method_map[role_user](
            active=active, add_perm=add_perm, save=save, **user_data
        )

    @classmethod
    def searcher_user(
        cls,
        save: bool,
        active: bool,
        add_perm: bool,
        **data: Dict[str, Any],
    ) -> Tuple[User, Model, Dict[str, Any]]:
        """
        This method creates a searcher user with the provided data.

        #### Parameters:
        - save: If the user should be saved in the database.
        - add_perm: If the user should have the permissions assigned.
        - active: If the user should be active.
        - data: The data to create the user.

        #### Returns:
        - A tuple of an instance of the user and searcher models or `None` and the
        user data.
        """

        base_user = None
        role_user = None
        data = cls._get_data(role_user=UserRoles.SEARCHER.value, **data)

        if save:
            base_user, role_user = cls._create_user(
                data={
                    "base_data": {
                        "email": data["email"],
                        "password": data["password"],
                    },
                    "role_data": {
                        "name": data["name"],
                        "last_name": data["last_name"],
                        "cc": data["cc"],
                        "address": data["address"],
                        "phone_number": data["phone_number"],
                    },
                },
                active=active,
                role_user=UserRoles.SEARCHER.value,
            )

            if add_perm:
                cls._assign_permissions(
                    user=base_user, role_user=UserRoles.SEARCHER.value
                )

        return base_user, role_user, data


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

    jwt_model = OutstandingToken
    blacklist_model = BlacklistedToken

    @staticmethod
    def _get_payload(
        token_type: str, exp: datetime, user_uuid: UserUUID, role_user: str
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
            "exp": datetime_to_epoch(dt=exp),
            "iat": datetime_to_epoch(dt=aware_utcnow()),
            "jti": uuid4().hex,
            "user_uuid": user_uuid,
            "role_user": role_user,
        }

    @classmethod
    def _create(
        cls,
        save: bool,
        user: User,
        role_user: str,
        add_blacklist: bool,
        token_type: str = None,
        exp: datetime = None,
        payload: JWTPayload = None,
    ) -> Dict[str, Any]:
        """
        This method creates a token with the provided parameters, returning the token and the payload.

        #### Parameters:
        - token_type: The type of token to create.
        - exp: The expiration date of the token.
        - role_user: The role of the user.
        - user: An instance of the User model.
        - save: If the token should be saved in the database.
        - payload: The payload of the token.
        """

        token_payload = (
            payload
            if payload
            else cls._get_payload(
                user_uuid=user.uuid.__str__(),
                token_type=token_type,
                role_user=role_user,
                exp=exp,
            )
        )

        token = encode(
            payload=token_payload,
            key=SIMPLE_JWT["SIGNING_KEY"],
            algorithm=SIMPLE_JWT["ALGORITHM"],
        )

        if save:
            token_obj = cls._save(user=user, payload=token_payload, token=token)

            if add_blacklist:
                cls._add_blacklist(token=token_obj)

        return {"token": token, "payload": token_payload}

    @classmethod
    def _save(
        cls, user: User, payload: JWTPayload, token: JSONWebToken
    ) -> OutstandingToken:
        """
        This method saves the token in the database.

        #### Parameters:
        - user: An instance of the User model.
        - payload: The payload of the token.
        - token: A JSONWebToken.
        """

        return cls.jwt_model.objects.create(
            user=user,
            jti=payload["jti"],
            token=token,
            created_at=timezone.now(),
            expires_at=datetime_from_epoch(ts=payload["exp"]),
        )

    @classmethod
    def _add_blacklist(cls, token: OutstandingToken) -> None:
        """
        Invalidates a JSON Web Token by adding it to the blacklist.
        """

        cls.blacklist_model.objects.create(token=token)

    @classmethod
    def _get_user(cls, save: bool, role_user: Optional[str]) -> User:
        """
        This method returns an instance of the User model that will be used to create
        a JSON Web Token.
        """

        if not save:
            return User()

        return UserFactory.user(
            role_user=role_user,
            active=True,
            add_perm=True,
            save=True,
        )[0]

    @classmethod
    def access(
        cls,
        exp: bool,
        save: bool,
        user: User = None,
        add_blacklist: bool = False,
        role_user: str = UserRoles.SEARCHER.value,
    ) -> Dict[str, Any]:
        """
        Creates an access token.

        #### Parameters:
        - exp: If the token should be expired.
        - role_user: The role of the user.
        - save: If the token should be saved in the database.
        - user: An instance of the User model.
        - add_blacklist: If the token should be added to the blacklist.
        """

        exp_token = (
            aware_utcnow() - ACCESS_TOKEN_LIFETIME
            if exp
            else aware_utcnow() + ACCESS_TOKEN_LIFETIME
        )

        return cls._create(
            user=(
                user if user else cls._get_user(role_user=role_user, save=save)
            ),
            role_user=role_user,
            save=save,
            token_type="access",
            add_blacklist=add_blacklist,
            exp=exp_token,
        )

    @classmethod
    def refresh(
        cls,
        exp: bool,
        save: bool,
        user: User = None,
        add_blacklist: bool = False,
        role_user: str = UserRoles.SEARCHER.value,
    ) -> Dict[str, Any]:
        """
        Creates a refresh token.

        #### Parameters:
        - exp: If the token should be expired.
        - role_user: The role of the user.
        - save: If the token should be saved in the database.
        - user: An instance of the User model.
        - add_blacklist: If the token should be added to the blacklist.
        """

        exp_token = (
            aware_utcnow() - REFRESH_TOKEN_LIFETIME
            if exp
            else aware_utcnow() + REFRESH_TOKEN_LIFETIME
        )

        return cls._create(
            user=(
                user if user else cls._get_user(role_user=role_user, save=save)
            ),
            role_user=role_user,
            token_type="refresh",
            exp=exp_token,
            save=save,
            add_blacklist=add_blacklist,
        )

    @classmethod
    def access_and_refresh(
        cls,
        save: bool,
        exp_access: bool,
        exp_refresh: bool,
        user: User = None,
        add_blacklist: bool = False,
        role_user: str = UserRoles.SEARCHER.value,
    ) -> Dict[str, Any]:
        """
        Creates an access and a refresh token.

        #### Parameters:
        - exp_access: If the access token should be expired.
        - exp_refresh: If the refresh token should be expired.
        - role: The role of the user.
        - save: If the token should be saved in the database.
        - user: An instance of the User model.
        - add_blacklist: If the token should be added to the blacklist.
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
        user_obj = (
            user if user else cls._get_user(role_user=role_user, save=save)
        )

        # Create the payloads
        refresh_payload = cls._get_payload(
            user_uuid=user_obj.uuid.__str__(),
            token_type="refresh",
            role_user=role_user,
            exp=exp_refresh,
        )
        access_payload = cls._get_payload(
            user_uuid=user_obj.uuid.__str__(),
            token_type="access",
            role_user=role_user,
            exp=exp_access,
        )
        access_payload["iat"] = refresh_payload["iat"]

        access_data = cls._create(
            payload=access_payload,
            role_user=role_user,
            user=user_obj,
            save=save,
            add_blacklist=add_blacklist,
        )
        refresh_data = cls._create(
            payload=refresh_payload,
            role_user=role_user,
            user=user_obj,
            save=save,
            add_blacklist=add_blacklist,
        )

        return {
            "tokens": {
                "access_token": access_data["token"],
                "refresh_token": refresh_data["token"],
            },
            "payloads": {
                "access_token": access_data["payload"],
                "refresh_token": refresh_data["payload"],
            },
        }

    @staticmethod
    def access_invalid() -> AccessToken:

        return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNzA5MDkxZjY1MDlU3IiwidXNlcl9pZCI6IjUwNTI5MjBjLWE3ZDYtNDM4ZS1iZmQwLWVhNTUyMTM4ODM2YrCZDFxbgBxhvNBJZsLzsyCn5pabwKKKSX9VKmQ8g"

    @staticmethod
    def refresh_invalid() -> RefreshToken:

        return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlCI6MTcwNToxNzA1ODcyMjgyLCJqdGkiOiI3YWRkNjhmNTczNjY0YzNjYTNmOWUyZGRmZjZkNTI4YyIsInVzZXJfaWQiOiI1ODllMGE1NC00YmFkLTRjNTAtYTVjMi03MWIzNzY2NzdjZjULS2WTFL3YiPh3YZD-oIxXDWICs3LJ-u9BQ"
