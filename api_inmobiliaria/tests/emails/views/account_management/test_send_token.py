from apps.utils.messages import ActivationErrors
from apps.api_exceptions import (
    DatabaseConnectionAPIError,
    ResourceNotFoundAPIError,
    AccountActivationAPIError,
)
from tests.factory import UserFactory
from rest_framework import status
from django.test import Client
from django.urls import reverse
from unittest.mock import Mock, patch
from uuid import uuid4
import pytest


@pytest.mark.django_db
class TestSendAccountActivationTokenAPIView:
    """
    This class encapsulates all tests for the view responsible for sending the account
    activation email to a user.
    """

    user_factory = UserFactory
    client = Client()

    def _get_path(self, **url_params) -> str:
        """
        This method returns the data needed to make a request to the view.
        """

        return reverse(
            viewname="send_activation_mail",
            kwargs={"user_uuid": url_params["user_uuid"]},
        )

    def test_if_valid_data(self) -> None:
        """
        This test is responsible for validating the expected behavior of the view
        when the request data is valid.
        """

        # Creating the user to be used in the test
        base_user, _, _ = self.user_factory.searcher_user(
            active=False, add_perm=False, save=True
        )

        # Simulating the request
        response = self.client.get(
            path=self._get_path(user_uuid=base_user.uuid),
            content_type="application/json",
        )

        # Asserting that response data is correct
        assert response.status_code == status.HTTP_200_OK

    def test_if_invalid_data(self) -> None:
        """
        This test is responsible for validating the expected behavior of the view
        when the request data is invalid.
        """

        # Simulating the request
        response = self.client.get(
            path=self._get_path(user_uuid="123456789"),
            content_type="application/json",
        )

        # Asserting that response data is correct
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_if_user_not_found(self) -> None:
        """
        This test is responsible for validating the expected behavior of the view
        when the user is not found in the database.
        """

        # Simulating the request
        response = self.client.get(
            path=self._get_path(user_uuid=uuid4()),
            content_type="application/json",
        )

        # Asserting that response data is correct
        status_code_expected = ResourceNotFoundAPIError.status_code
        response_code_expected = "user_not_found"
        response_data_expected = ActivationErrors.USER_NOT_FOUND.value

        assert response.status_code == status_code_expected
        assert response.data["code"] == response_code_expected
        assert response.data["detail"] == response_data_expected

    def test_if_user_already_active(self) -> None:
        """
        This test is responsible for validating the expected behavior of the view
        when the user is already active.
        """

        # Creating the user to be used in the test
        base_user, _, _ = self.user_factory.searcher_user(
            active=True, add_perm=False, save=True
        )

        # Simulating the request
        response = self.client.get(
            path=self._get_path(user_uuid=base_user.uuid),
            content_type="application/json",
        )

        # Asserting that response data is correct
        status_code_expected = AccountActivationAPIError.status_code
        response_code_expected = AccountActivationAPIError.default_code
        response_data_expected = ActivationErrors.ACTIVE_ACCOUNT.value

        assert response.status_code == status_code_expected
        assert response.data["code"] == response_code_expected
        assert response.data["detail"] == response_data_expected

    @patch(
        "apps.emails.infrastructure.views.account_management.send_token.TokenRepository"
    )
    def test_if_conection_db_failed(
        self,
        token_repository_mock: Mock,
    ) -> None:
        """
        Test that validates the expected behavior of the view when the connection to
        the database fails.
        """

        # Creating the user to be used in the test
        base_user, _, _ = self.user_factory.searcher_user(
            active=False, add_perm=False, save=True
        )

        # Mocking the methods
        create: Mock = token_repository_mock.create
        create.side_effect = DatabaseConnectionAPIError

        # Simulating the request
        response = self.client.get(
            path=self._get_path(user_uuid=base_user.uuid),
            content_type="application/json",
        )

        # Asserting that response data is correct
        status_code_expected = DatabaseConnectionAPIError.status_code
        response_code_expected = DatabaseConnectionAPIError.default_code
        response_data_expected = DatabaseConnectionAPIError.default_detail

        assert response.status_code == status_code_expected
        assert response.data["code"] == response_code_expected
        assert response.data["detail"] == response_data_expected
