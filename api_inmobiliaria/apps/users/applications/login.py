from apps.utils.messages import JWTErrorMessages
from apps.users.domain.constants import USER_ROLE_PERMISSIONS
from apps.users.models import BaseUser
from apps.api_exceptions import (
    PermissionDeniedAPIError,
    AuthenticationFailedAPIError,
)
from authentication.jwt import AccessToken, RefreshToken
from django.contrib.auth import authenticate
from typing import Dict


class JWTLogin:
    """
    This class encapsulates the use cases given to JSON Web Tokens in the system
    related to user authentication.
    """

    refresh_token_class = RefreshToken
    access_token_class = AccessToken

    @classmethod
    def authenticate_user(cls, credentials: Dict[str, str]) -> Dict[str, str]:
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

        base_user: BaseUser | None = authenticate(**credentials)

        if not base_user:
            raise AuthenticationFailedAPIError(
                detail=JWTErrorMessages.AUTHENTICATION_FAILED.value,
            )
        elif not base_user.is_active:
            raise AuthenticationFailedAPIError(
                detail=JWTErrorMessages.INACTIVE_ACCOUNT.value,
            )

        user_role = base_user.content_type.model

        if not base_user.has_perm(
            perm=USER_ROLE_PERMISSIONS[user_role]["jwt_auth"]
        ):
            raise PermissionDeniedAPIError()

        refresh_token = cls.refresh_token_class(base_user=base_user)
        access_token = cls.access_token_class(
            base_user=base_user, refresh_token=refresh_token
        )

        return {
            "access_token": str(access_token),
            "refresh_token": str(refresh_token),
            "user_role": user_role,
        }
