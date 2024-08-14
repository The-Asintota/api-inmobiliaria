from apps.users.infrastructure.serializers import AuthenticationSerializer
from apps.users.domain.constants import UserProperties
from apps.constants import ERROR_MESSAGES
from tests.utils import fake
from typing import Dict, List
import pytest


class TestAuthenticationSerializer:
    """
    This class encapsulates the serializer tests in charge of validating the data
    required for a user to authenticate in the system.
    """

    serializer_class = AuthenticationSerializer

    def test_valid_data(self) -> None:
        """
        This test is responsible for validating the expected behavior of the
        serializer when the log data is valid.
        """

        data = {
            "email": "user1@email.com",
            "password": "contraseña1234",
        }

        serializer = self.serializer_class(data=data)

        # Asserting that the serializer is valid and the data is correct
        assert serializer.is_valid()

        for field, value in data.items():
            assert serializer.validated_data[field] == value

    @pytest.mark.parametrize(
        argnames="data, error_messages",
        argvalues=[
            (
                {},
                {
                    "email": [ERROR_MESSAGES["required"]],
                    "password": [ERROR_MESSAGES["required"]],
                },
            ),
            (
                {
                    "email": f"user{fake.random_number(digits=41)}@email.com",
                    "password": fake.password(length=41, special_chars=True),
                },
                {
                    "email": [
                        ERROR_MESSAGES["max_length"].format(
                            max_length=UserProperties.EMAIL_MAX_LENGTH.value,
                        ),
                    ],
                    "password": [
                        ERROR_MESSAGES["max_length"].format(
                            max_length=UserProperties.PASSWORD_MAX_LENGTH.value,
                        ),
                    ],
                },
            ),
        ],
        ids=["missing_fields", "max_length_data"],
    )
    def test_invalid_data(
        self,
        data: Dict[str, str],
        error_messages: Dict[str, List],
    ) -> None:
        """
        This test is responsible for validating the expected behavior of the
        serializer when the log data is invalid.
        """

        serializer = self.serializer_class(data=data)

        # Asserting that the serializer is not valid and the errors are correct
        assert not serializer.is_valid()
        assert serializer.validated_data == {}

        errors_formated = {
            field: [str(error) for error in errors]
            for field, errors in serializer.errors.items()
        }

        for field, message in error_messages.items():
            assert errors_formated[field] == message
