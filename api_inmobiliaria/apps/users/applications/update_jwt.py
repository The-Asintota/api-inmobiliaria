from apps.users.domain.abstractions import IJWTRepository, IUserRepository
from apps.users.domain.typing import JSONWebToken
from apps.api_exceptions import ResourceNotFoundAPIError
from apps.utils.messages import JWTErrorMessages
from authentication.jwt import AccessToken, RefreshToken
from typing import Dict


class JWTUpdate:
    """
    This class encapsulates the use cases given to JSON Web Tokens in the system.
    """

    refresh_token_class = RefreshToken
    access_token_class = AccessToken

    def __init__(
        self, jwt_repository: IJWTRepository, user_repository: IUserRepository
    ) -> None:
        self._jwt_repository = jwt_repository
        self._user_repository = user_repository

    def new_tokens(
        self, refresh_token: RefreshToken
    ) -> Dict[str, JSONWebToken]:
        """
        Update the user's access and refresh tokens.

        #### Parameters:
        - refresh_token: A RefreshToken instance.

        #### Raises:
        - ResourceNotFoundAPIError: If the user does not exist.
        """

        base_user = self._user_repository.get_base_data(
            uuid=refresh_token.payload["user_uuid"],
            is_active=True,
            is_deleted=False,
        )

        if not base_user:
            message = JWTErrorMessages.USER_NOT_FOUND.value

            raise ResourceNotFoundAPIError(
                code=message["code"],
                detail=message["detail"],
            )

        refresh_token.blacklist()

        new_refresh_token = self.refresh_token_class(base_user=base_user)
        new_access_token = self.access_token_class(
            base_user=base_user, refresh_token=new_refresh_token
        )

        return {
            "access_token": str(new_access_token),
            "refresh_token": str(new_refresh_token),
        }
