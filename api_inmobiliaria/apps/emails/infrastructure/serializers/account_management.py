from apps.users.domain.typing import UserUUID
from apps.emails.utils import decode_b64
from apps.utils import is_valid_uuid
from rest_framework import serializers
import base64


class Base64UserTokenSerializer(serializers.Serializer):
    """
    Serializer that validates and decodes user UUIDs in base 64 and a token. This data
    is used in account management processes for a user.
    """

    user_uuidb64 = serializers.CharField(max_length=100, required=True)
    token = serializers.CharField(max_length=100, required=True)

    @staticmethod
    def _is_base64(s: str) -> bool:
        """
        Check if the provided string is a valid base64 string.
        """

        try:
            return base64.b64encode(base64.b64decode(s)).decode() == s
        except Exception:

            return False

    def validate_user_uuidb64(self, value: str) -> UserUUID:
        if not self._is_base64(s=value):
            raise serializers.ValidationError(
                code="invalid_data", detail="Invalid user uuidb64."
            )

        user_uuid = decode_b64(s=value)

        if not is_valid_uuid(value=user_uuid):
            raise serializers.ValidationError(
                code="invalid_data", detail="Invalid user uuid."
            )

        return user_uuid
