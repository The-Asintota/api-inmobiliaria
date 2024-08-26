from apps.users.domain.typing import UserUUID
from apps.utils.generators import decode_b64
from apps.utils.validators import is_valid_uuid, is_base64
from rest_framework import serializers


class Base64UserTokenSerializer(serializers.Serializer):
    """
    Serializer that validates and decodes user UUIDs in base 64 and a token. This data
    is used in account management processes for a user.
    """

    user_uuidb64 = serializers.CharField(max_length=100, required=True)
    token = serializers.CharField(max_length=100, required=True)

    def validate_user_uuidb64(self, value: str) -> UserUUID:
        """
        Validate the user UUID in base 64 format.
        """

        if not is_base64(value=value):
            raise serializers.ValidationError(
                code="invalid_data", detail="Invalid user uuidb64."
            )

        user_uuid = decode_b64(s=value)

        if not is_valid_uuid(value=user_uuid):
            raise serializers.ValidationError(
                code="invalid_data", detail="Invalid user uuid."
            )

        return user_uuid
