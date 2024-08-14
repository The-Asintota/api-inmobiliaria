from apps.users.infrastructure.serializers import (
    JWTErrorMessages as SerializerErrorMessages,
    LogoutSerializer,
)
from tests.factory import JWTFactory
from rest_framework.fields import CharField
from typing import Dict, List
import pytest


# This constant is used when the serializer error messages are the default.
DEFAULT_ERROR_MESSAGES = CharField().error_messages


class TestLogoutSerializer:
    """
    This class encapsulates all the tests of the serializer in charge of validating
    the data required to log out a user.
    """

    serializer_class = LogoutSerializer
    jwt_factory = JWTFactory

    def test_valid_data(self) -> None:
        """
        This test is responsible for validating the expected behavior of the
        serializer when the log out data is valid.
        """

        # Creating JWTs to be used in the test
        data = self.jwt_factory.access_and_refresh(
            role="AnyUser", exp_access=False, exp_refresh=False, save=False
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
                    "refresh": [SerializerErrorMessages.REFRESH_INVALID.value],
                    "access": [SerializerErrorMessages.ACCESS_INVALID.value],
                },
            ),
            (
                JWTFactory.access_and_refresh(
                    role="AnyUser",
                    exp_access=True,
                    exp_refresh=True,
                    save=False,
                ).get("tokens"),
                {
                    "access": [SerializerErrorMessages.ACCESS_EXPIRED.value],
                    "refresh": [SerializerErrorMessages.REFRESH_EXPIRED.value],
                },
            ),
        ],
        ids=[
            "empty_data",
            "tokens_invalid",
            "tokens_expired",
        ],
    )
    def test_invalid_data(
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
