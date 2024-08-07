from apps.users.domain.constants import UserRoles, USER_ROLE_PERMISSIONS
from apps.users.domain.typing import JSONWebToken, JWTPayload
from apps.users.domain.abstractions import (
    IJWTRepository,
    ITokenClass,
    IUserRepository,
)
from apps.users.models import User, JWT
from apps.api_exceptions import (
    JWTAPIError,
    ResourceNotFoundAPIError,
    PermissionDeniedAPIError,
    AuthenticationFailedAPIError,
)
from django.contrib.auth import authenticate
from typing import Dict, List
from enum import Enum


class JWTErrorMessages(Enum):
    """
    Enum class for error messages related to JWT use cases. The errors that are in
    Spanish are messages that the user will see.
    """

    AUTHENTICATION_FAILED = "Credenciales inválidas."
    INACTIVE_ACCOUNT = "Cuenta del usuario inactiva."
    JWT_ERROR = "The JWTs sent do not match the user's last tokens."
    TOKEN_NOT_FOUND_CODE = "token_not_found"
    TOKEN_NOT_FOUND = "JWT not found."
    USER_NOT_FOUND_CODE = "user_not_found"
    USER_NOT_FOUND = "The JWT user does not exist."


class JWTUsesCases:
    """
    This class encapsulates the use cases given to JSON Web Tokens in the system.
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
        - ResourceNotFoundAPIError: If the tokens do not exist.
        - JWTAPIError: If the tokens do not match the user's last tokens.
        """

        latest_tokens = self.__jwt_repository.get(user=user)

        if latest_tokens.count() < 2:
            raise ResourceNotFoundAPIError(
                code=JWTErrorMessages.TOKEN_NOT_FOUND_CODE.value,
                detail=JWTErrorMessages.TOKEN_NOT_FOUND.value,
            )

        payload_jtis = {access_payload["jti"], refresh_payload["jti"]}
        token_jtis = {token.jti for token in latest_tokens}

        if not payload_jtis.issubset(token_jtis):
            raise JWTAPIError(
                detail=JWTErrorMessages.JWT_ERROR.value,
            )

        return latest_tokens

    def authenticate_user(
        self, credentials: Dict[str, str]
    ) -> Dict[str, JSONWebToken]:
        """
        Authenticate a user with the given credentials and return access and refresh
        tokens.

        #### Parameters:
        - credentials: A dictionary containing the user's credentials.

        #### Raises:
        - AuthenticationFailedAPIError: If the credentials are invalid or the user is
        inactive.
        - PermissionDeniedAPIError: If the user does not have the required permissions.
        """

        user = authenticate(**credentials)

        if not user:
            raise AuthenticationFailedAPIError(
                detail=JWTErrorMessages.AUTHENTICATION_FAILED.value,
            )
        elif not user.is_active:
            raise AuthenticationFailedAPIError(
                detail=JWTErrorMessages.INACTIVE_ACCOUNT.value,
            )
        elif not user.has_perm(
            perm=USER_ROLE_PERMISSIONS[UserRoles.SEARCHER.value]["jwt"]
        ):
            raise PermissionDeniedAPIError()

        access, refresh = self.__jwt_class.get_token(user=user)

        return {"access": access, "refresh": refresh}

    def update_tokens(
        self, data: Dict[str, JWTPayload]
    ) -> Dict[str, JSONWebToken]:
        """
        Update the user's access and refresh tokens.

        #### Parameters:
        - data: A dictionary containing the access and refresh token payloads.

        #### Raises:
        - ResourceNotFoundAPIError: If the user does not exist.
        """

        user = self.__user_repository.get_user_data(
            uuid=data["access"]["user_uuid"],
            is_active=True,
            is_deleted=False,
        ).first()

        if not user:
            raise ResourceNotFoundAPIError(
                code=JWTErrorMessages.USER_NOT_FOUND_CODE.value,
                detail=JWTErrorMessages.USER_NOT_FOUND.value,
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
        - ResourceNotFoundAPIError: If the user does not exist.
        """

        user = self.__user_repository.get_user_data(
            uuid=data["access"]["user_uuid"],
            is_active=True,
            is_deleted=False,
        ).first()

        if not user:
            raise ResourceNotFoundAPIError(
                code=JWTErrorMessages.USER_NOT_FOUND_CODE.value,
                detail=JWTErrorMessages.USER_NOT_FOUND.value,
            )

        tokens = self.__is_token_recent(
            access_payload=data["access"],
            refresh_payload=data["refresh"],
            user=user,
        )

        for token in tokens:
            if not token.is_expired():
                self.__jwt_repository.add_to_blacklist(token=token)
