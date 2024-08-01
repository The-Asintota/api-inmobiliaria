from apps.users.domain.constants import UserRoles, USER_ROLE_PERMISSIONS
from apps.users.domain.typing import JWToken, JWTPayload
from apps.users.domain.abstractions import (
    IJWTRepository,
    ITokenClass,
    IUserRepository,
)
from apps.users.models import User, JWT
from apps.exceptions import JWTError, ResourceNotFoundError, PermissionDenied
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from django.contrib.auth import authenticate
from typing import Dict, List


class JWTUsesCases:
    """
    Use cases for the JWT tokens. It contains the business logic for the operations
    that can be performed with the JWT tokens.
    """

    def __init__(
        self,
        jwt_class: ITokenClass = None,
        jwt_repository: IJWTRepository = None,
        user_repository: IUserRepository = None,
    ) -> None:
        self.__user_repository = user_repository
        self.__jwt_repository = jwt_repository
        self.__jwt_class = jwt_class

    def __is_token_recent(
        self,
        user: User,
        access_payload: JWTPayload,
        refresh_payload: JWTPayload,
    ) -> List[JWT]:
        """
        Verifies if the tokens provided are the last generated tokens of the user.

        #### Parameters:
        - access_payload: The payload of the access token.
        - refresh_payload: The payload of the refresh token.
        - user: An instance of the User model.

        #### Raises:
        - ResourceNotFoundError: If the tokens do not exist.
        - JWTError: If the tokens do not match the user's last tokens.
        """

        latest_tokens = self.__jwt_repository.get(user=user)

        if latest_tokens.count() < 2:
            raise ResourceNotFoundError(
                code="token_not_found", detail="JSON Web Tokens not found."
            )

        payload_jtis = {access_payload["jti"], refresh_payload["jti"]}
        token_jtis = {token.jti for token in latest_tokens}

        if not payload_jtis.issubset(token_jtis):
            raise JWTError(
                code="token_error",
                detail="The JSON Web Tokens does not match the user's last tokens.",
            )

        return latest_tokens

    def authenticate_user(
        self, credentials: Dict[str, str]
    ) -> Dict[str, JWToken]:
        """
        Authenticate a user with the given credentials and return access and refresh
        tokens.

        #### Parameters:
        - credentials: A dictionary containing the user's credentials.

        #### Raises:
        - AuthenticationFailed: If the credentials are invalid or the user is
        inactive.
        - PermissionDenied: If the user does not have the required permissions.
        """

        user = authenticate(**credentials)

        if not user:
            raise AuthenticationFailed(
                code="authentication_failed",
                detail="Credenciales inválidas.",
            )
        elif not user.is_active:
            raise AuthenticationFailed(
                code="authentication_failed",
                detail="Cuenta del usuario inactiva.",
            )
        elif not user.has_perm(
            perm=USER_ROLE_PERMISSIONS[UserRoles.SEARCHER.value]["jwt"]
        ):
            raise PermissionDenied()

        access, refresh = self.__jwt_class.get_token(user=user)

        return {"access": access, "refresh": refresh}

    def update_tokens(self, data: Dict[str, JWTPayload]) -> Dict[str, JWToken]:
        """
        Update the user's access and refresh tokens.

        #### Parameters:
        - data: A dictionary containing the access and refresh token payloads.

        #### Raises:
        - ResourceNotFoundError: If the user does not exist.
        """

        user = self.__user_repository.get_user_data(
            uuid=data["access"]["user_uuid"]
        ).first()

        if not user:
            raise ResourceNotFoundError(
                code="user_not_found",
                detail="The JSON Web Token user does not exist.",
            )

        tokens = self.__is_token_recent(
            access_payload=data["access"],
            refresh_payload=data["refresh"],
            user=user,
        )

        for token in tokens:
            if not token.is_expired():
                self.__jwt_repository.add_to_blacklist(token=token)

        access, refresh = self.__jwt_class.get_token(user=user)

        return {"access": access, "refresh": refresh}

    def logout_user(self, data: Dict[str, JWTPayload]) -> None:
        """
        Logout a user by adding the remaining tokens to expire to the blacklist.

        #### Parameters:
        - data: A dictionary containing the access and refresh token payloads.

        #### Raises:
        - ResourceNotFoundError: If the user does not exist.
        """

        user = self.__user_repository.get_user_data(
            uuid=data["access"]["user_uuid"]
        ).first()

        if not user:
            raise ResourceNotFoundError(
                code="user_not_found",
                detail="The JSON Web Token user does not exist.",
            )

        tokens = self._is_token_recent(
            access_payload=data["access"],
            refresh_payload=data["refresh"],
            user=user,
        )

        for token in tokens:
            if not token.is_expired():
                self.__jwt_repository.add_to_blacklist(token=token)
