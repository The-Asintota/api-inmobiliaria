from apps.users.infrastructure.serializers import (
    LogoutSerializer,
    JWTSerializerErrorMessages,
)
from tests.factory import JWTFactory
from rest_framework.fields import CharField
from typing import Dict, List
import pytest


# This constant is used when the serializer error messages are the default.
DEFAULT_ERROR_MESSAGES = CharField().error_messages


class TestSerializer:
    """
    This class encapsulates all the tests of the serializer in charge of validating
    the data required to log out a user.
    """

    serializer_class = LogoutSerializer

    def test_correct_execution(self) -> None:
        """
        This test is responsible for validating the expected behavior of the
        serializer when the log out data is valid.
        """

        data = JWTFactory.access_and_refresh(
            exp_access=False, exp_refresh=False
        )
        serializer = self.serializer_class(data=data["tokens"])

        # Check if the serializer is valid
        assert serializer.is_valid()

        # Check if the serializer has the correct validated data
        for key, value in data["payloads"]["access"].items():
            assert serializer.validated_data["access"][key] == value
        for key, value in data["payloads"]["refresh"].items():
            assert serializer.validated_data["refresh"][key] == value

    @pytest.mark.parametrize(
        argnames="data, error_messages",
        argvalues=[
            (
                {},
                {
                    "refresh": [DEFAULT_ERROR_MESSAGES["required"]],
                    "access": [DEFAULT_ERROR_MESSAGES["required"]],
                },
            ),
            (
                {
                    "refresh": JWTFactory.refresh_invalid(),
                    "access": JWTFactory.access_invalid(),
                },
                {
                    "refresh": [
                        JWTSerializerErrorMessages.REFRESH_INVALID.value
                    ],
                    "access": [JWTSerializerErrorMessages.ACCESS_INVALID.value],
                },
            ),
            (
                {
                    "refresh": JWTFactory.refresh(exp=True).get("token"),
                },
                {
                    "access": [DEFAULT_ERROR_MESSAGES["required"]],
                    "refresh": [
                        JWTSerializerErrorMessages.REFRESH_EXPIRED.value
                    ],
                },
            ),
        ],
        ids=[
            "empty_data",
            "tokens_invalid",
            "refresh_expired",
        ],
    )
    def test_failed_execution(
        self, data: Dict[str, str], error_messages: Dict[str, List]
    ) -> None:
        """
        This test is responsible for validating the expected behavior of the
        serializer when the log out data is invalid.
        """

        serializer = self.serializer_class(data=data)

        # Check if the serializer is not valid
        assert not serializer.is_valid()
        assert serializer.validated_data == {}

        # Check if the serializer has the correct error messages
        serializer_errors_formated = {
            field: [str(error) for error in errors]
            for field, errors in serializer.errors.items()
        }

        for field, message in error_messages.items():
            assert serializer_errors_formated[field] == message
