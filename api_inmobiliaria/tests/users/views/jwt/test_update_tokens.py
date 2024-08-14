from apps.users.infrastructure.serializers import (
    JWTErrorMessages as SerializerErrorMessages,
)
from apps.users.applications import JWTErrorMessages
from apps.users.models import User
from apps.api_exceptions import (
    DatabaseConnectionAPIError,
    ResourceNotFoundAPIError,
    JWTAPIError,
)
from tests.factory import JWTFactory, UserFactory
from tests.utils import empty_queryset
from rest_framework import status
from rest_framework.fields import CharField
from django.test import Client
from django.urls import reverse
from unittest.mock import Mock, patch
from typing import Dict, List
import pytest


# This constant is used when the serializer error messages are the default.
DEFAULT_ERROR_MESSAGES = CharField().error_messages


@pytest.mark.django_db
class TestUpdateTokensAPIView:
    """
    This class encapsulates all the tests of the view in charge of handling requests
    for the creation of new JWTs when the access token has expired.

    In order for the user to keep his session active, new JWTs can be generated using
    the refresh token, as long as the access token has expired.
    """

    path = reverse(viewname="update_jwt")
    user_factory = UserFactory
    jwt_factory = JWTFactory
    client = Client()

    def test_request_valid_data(self) -> None:
        """
        This test is responsible for validating the expected behavior of the view
        when the request data is valid.
        """

        # Creating the user data and the JWTs to be used in the test
        user, _ = self.user_factory.create_searcher_user(
            active=True, save=True, add_perm=False
        )
        jwt_data = self.jwt_factory.access_and_refresh(
            user=user,
            role="AnyUser",
            exp_access=True,
            exp_refresh=False,
            save=True,
        )

        # Simulating the request
        response = self.client.post(
            path=self.path,
            data=jwt_data["tokens"],
            content_type="application/json",
        )

        # Asserting that response data is correct
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

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
                    exp_access=False,
                    exp_refresh=True,
                    save=False,
                ).get("tokens"),
                {
                    "refresh": [SerializerErrorMessages.REFRESH_EXPIRED.value],
                },
            ),
            (
                JWTFactory.access_and_refresh(
                    role="AnyUser",
                    exp_access=False,
                    exp_refresh=False,
                    save=False,
                ).get("tokens"),
                {
                    "access": [
                        SerializerErrorMessages.ACCESS_NOT_EXPIRED.value
                    ],
                },
            ),
        ],
        ids=[
            "empty_data",
            "tokens_invalid",
            "refresh_expired",
            "access_not_expired",
        ],
    )
    def test_request_invalid_data(
        self,
        data: Dict[str, str],
        error_messages: Dict[str, List],
    ) -> None:
        """
        This test is responsible for validating the expected behavior of the view
        when the request data is invalid.
        """

        # Simulating the request
        response = self.client.post(
            path=self.path,
            data=data,
            content_type="application/json",
        )

        # Asserting that response data is correct
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["code"] == "invalid_request_data"

        # Asserting that the error messages are correct
        response_errors_formated = {
            field: [str(error) for error in errors]
            for field, errors in response.data["detail"].items()
        }

        for field, message in error_messages.items():
            assert response_errors_formated[field] == message

    def test_if_token_not_found(self) -> None:
        """
        This test is responsible for validating the expected behavior of the view
        when the JWTs are not found in the database.
        """

        # Creating the user data and the JWTs to be used in the test
        user, _ = self.user_factory.create_searcher_user(
            active=True, save=True, add_perm=False
        )
        jwt_data = self.jwt_factory.access_and_refresh(
            user=user,
            role="AnyUser",
            exp_access=True,
            exp_refresh=False,
            save=False,
        )

        # Simulating the request
        response = self.client.post(
            path=self.path,
            data=jwt_data["tokens"],
            content_type="application/json",
        )

        # Asserting that response data is correct
        status_code_expected = ResourceNotFoundAPIError.status_code
        response_code_expected = JWTErrorMessages.TOKEN_NOT_FOUND_CODE.value
        response_data_expected = JWTErrorMessages.TOKEN_NOT_FOUND.value

        assert response.status_code == status_code_expected
        assert response.data["code"] == response_code_expected
        assert response.data["detail"] == response_data_expected

    def test_if_tokens_not_match_user_last_tokens(self) -> None:
        """
        This test is responsible for validating the expected behavior of the view
        when the JWTs do not match the user.
        """

        # Creating the user data and the JWTs to be used in the test
        user, _ = self.user_factory.create_searcher_user(
            active=True, save=True, add_perm=False
        )
        jwt_data = self.jwt_factory.access_and_refresh(
            user=user,
            role="AnyUser",
            exp_access=True,
            exp_refresh=False,
            save=False,
        )

        # Other tokens are created in order to raise the exception
        _ = self.jwt_factory.access_and_refresh(
            user=user,
            role="AnyUser",
            exp_access=True,
            exp_refresh=False,
            save=True,
        )

        # Simulating the request
        response = self.client.post(
            path=self.path,
            data=jwt_data["tokens"],
            content_type="application/json",
        )

        # Asserting that response data is correct
        status_code_expected = JWTAPIError.status_code
        response_code_expected = JWTAPIError.default_code
        response_data_expected = JWTErrorMessages.JWT_ERROR.value

        assert response.status_code == status_code_expected
        assert response.data["code"] == response_code_expected
        assert response.data["detail"] == response_data_expected

    @patch("apps.users.infrastructure.views.jwt.UserRepository")
    def test_if_user_not_found(self, user_repository_mock: Mock) -> None:
        """
        This test is responsible for validating the expected behavior of the view
        when the user is not found in the database.
        """

        # Mocking the methods
        get_user_data: Mock = user_repository_mock.get_user_data
        get_user_data.return_value = empty_queryset(model=User)

        # Creating the JWTs to be used in the test
        jwt_data = self.jwt_factory.access_and_refresh(
            user=User(),
            role="AnyUser",
            exp_access=True,
            exp_refresh=False,
            save=False,
        )

        # Simulating the request
        response = self.client.post(
            path=self.path,
            data=jwt_data["tokens"],
            content_type="application/json",
        )

        # Asserting that response data is correct
        status_code_expected = ResourceNotFoundAPIError.status_code
        response_code_expected = JWTErrorMessages.USER_NOT_FOUND_CODE.value
        response_data_expected = JWTErrorMessages.USER_NOT_FOUND.value

        assert response.status_code == status_code_expected
        assert response.data["code"] == response_code_expected
        assert response.data["detail"] == response_data_expected

    @patch("apps.users.infrastructure.views.jwt.UserRepository")
    def test_if_conection_db_failed(self, user_repository_mock: Mock) -> None:
        """
        Test that validates the expected behavior of the view when the connection to
        the database fails.
        """

        # Mocking the methods
        get_user_data: Mock = user_repository_mock.get_user_data
        get_user_data.side_effect = DatabaseConnectionAPIError

        # Creating the JWTs to be used in the test
        jwt_data = self.jwt_factory.access_and_refresh(
            user=User(),
            role="AnyUser",
            exp_access=True,
            exp_refresh=False,
            save=False,
        )

        # Simulating the request
        response = self.client.post(
            path=self.path,
            data=jwt_data["tokens"],
            content_type="application/json",
        )

        # Asserting that response data is correct
        status_code_expected = DatabaseConnectionAPIError.status_code
        response_code_expected = DatabaseConnectionAPIError.default_code
        response_data_expected = DatabaseConnectionAPIError.default_detail

        assert response.status_code == status_code_expected
        assert response.data["code"] == response_code_expected
        assert response.data["detail"] == response_data_expected
