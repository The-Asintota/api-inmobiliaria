from apps.users.models import BaseUser
from django.contrib.auth.tokens import PasswordResetTokenGenerator
import base64
import six


def decode_b64(s: str) -> str:
    """
    Decodes a base64-encoded string and returns the result as a string.
    """

    decoded_bytes = base64.b64decode(s)

    return decoded_bytes.decode("utf-8")


class TokenGenerator(PasswordResetTokenGenerator):
    """
    TokenGenerator is a class that generates a token, the token is a unique identifier
    that ensures the security and validity of the processes initiated.

    It is used in scenarios where a user needs to interact with the system via email,
    ensuring that the user is indeed the one who initiated the process.
    """

    def _make_hash_value(self, base_user: BaseUser, timestamp: int) -> str:
        """
        Create a hash value using the user's id, timestamp, and active status.
        """

        return (
            six.text_type(base_user.uuid)
            + six.text_type(timestamp)
            + six.text_type(base_user.is_active)
        )

    def make_token(self, base_user: BaseUser) -> str:
        """
        Generate a token for the given user.

        #### Parameters:
        - user: A instance of the BaseUser model.
        """

        token = self._make_token_with_timestamp(
            base_user,
            self._num_seconds(self._now()),
            self.secret,
        )

        return token
