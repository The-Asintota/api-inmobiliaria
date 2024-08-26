from authentication.jwt import AccessToken, RefreshToken, Token
from typing import Dict


class JWTLogout:
    """
    This class encapsulates the use cases given to JSON Web Tokens in the system.
    """

    @classmethod
    def logout_user(cls, data: Dict[str, Token]) -> None:
        """
        Logout a user by adding the tokens to the blacklist.

        #### Parameters:
        - data: A dictionary containing the access and refresh token payloads.
        - user: An instance of the BaseUser model.
        """

        refresh_token: AccessToken = data["refresh_token"]
        accress_token: RefreshToken = data["access_token"]

        refresh_token.blacklist()
        accress_token.blacklist()
