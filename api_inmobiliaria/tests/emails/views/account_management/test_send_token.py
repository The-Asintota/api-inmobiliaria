from apps.users.domain.constants import UserRoles
from apps.users.domain.typing import UserUUID
from apps.users.models import User
from apps.emails.applications import ActivationErrors
from apps.api_exceptions import (
    DatabaseConnectionAPIError,
    ResourceNotFoundAPIError,
    AccountActivationAPIError,
)
from django.test import Client
from django.urls import reverse
from unittest.mock import Mock, patch
from typing import Callable, Tuple, Dict
from uuid import uuid4
import pytest


@pytest.fixture
def setUp() -> Callable[[UserUUID, str], Tuple[Client, str]]:
    """
    A fixture to set up the client and the path for the view.
    """

    def get_data_request(
        user_uuid: UserUUID, viewname: str
    ) -> Tuple[Client, str]:

        return Client(), reverse(
            viewname=viewname, kwargs={"user_uuid": user_uuid}
        )

    return get_data_request


class TestSendAccountActivationTokenAPIView:
    """
    This class encapsulates all tests for the view responsible for sending the account
    activation email to a user.
    """

    viewname = "send_activation_mail"

    @pytest.mark.django_db
    def test_request_valid(
        self,
        setUp: Callable[[UserUUID, str], Tuple[Client, str]],
        create_user: Callable[[bool, str, bool], Tuple[User, Dict[str, Dict]]],
    ) -> None:
        """
        This test is responsible for validating the expected behavior of the view
        when the request data is valid.
        """

        # Creating a user
        user, _ = create_user(
            active=False, role=UserRoles.SEARCHER.value, add_perm=False
        )

        # Simulating the request
        client, path = setUp(viewname=self.viewname, user_uuid=user.uuid)
        response = client.get(
            path=path,
            content_type="application/json",
        )

        # Asserting that response data is correct
        assert response.status_code == 200

    def test_request_invalid(
        self,
        setUp: Callable[[UserUUID, str], Tuple[Client, str]],
    ) -> None:
        """
        This test is responsible for validating the expected behavior of the view
        when the request data is invalid.
        """

        # Simulating the request
        client, path = setUp(viewname=self.viewname, user_uuid="123456789")
        response = client.get(
            path=path,
            content_type="application/json",
        )

        # Asserting that response data is correct
        assert response.status_code == 400

    @pytest.mark.django_db
    def test_if_user_not_found(
        self,
        setUp: Callable[[UserUUID, str], Tuple[Client, str]],
    ) -> None:
        """
        This test is responsible for validating the expected behavior of the view
        when the user is not found in the database.
        """

        # Simulating the request
        client, path = setUp(viewname=self.viewname, user_uuid=uuid4())
        response = client.get(
            path=path,
            content_type="application/json",
        )

        # Asserting that response data is correct
        assert response.status_code == ResourceNotFoundAPIError.status_code
        assert response.data["code"] == "user_not_found"
        assert response.data["detail"] == ActivationErrors.USER_NOT_FOUND.value

    @pytest.mark.django_db
    def test_if_user_already_active(
        self,
        setUp: Callable[[UserUUID, str], Tuple[Client, str]],
        create_user: Callable[[bool, str, bool], Tuple[User, Dict[str, Dict]]],
    ) -> None:
        """
        This test is responsible for validating the expected behavior of the view
        when the user is already active.
        """

        # Creating a user
        user, _ = create_user(
            active=True, role=UserRoles.SEARCHER.value, add_perm=False
        )

        # Simulating the request
        client, path = setUp(viewname=self.viewname, user_uuid=user.uuid)
        response = client.get(
            path=path,
            content_type="application/json",
        )

        # Asserting that response data is correct
        assert response.status_code == AccountActivationAPIError.status_code
        assert response.data["code"] == AccountActivationAPIError.default_code
        assert response.data["detail"] == ActivationErrors.ACTIVE_ACCOUNT.value

    @pytest.mark.django_db
    @patch(
        "apps.emails.infrastructure.views.account_management.send_token.TokenRepository"
    )
    def test_if_db_connection_fails(
        self,
        token_repository_mock: Mock,
        setUp: Callable[[UserUUID, str], Tuple[Client, str]],
        create_user: Callable[[bool, str, bool], Tuple[User, Dict[str, Dict]]],
    ) -> None:
        """
        Test to check if the response is correct when an exception is raised.
        """

        # Creating a user
        user, _ = create_user(
            active=False, role=UserRoles.SEARCHER.value, add_perm=False
        )

        # Mocking the methods
        create: Mock = token_repository_mock.create
        create.side_effect = DatabaseConnectionAPIError

        # Simulating the request
        client, path = setUp(viewname=self.viewname, user_uuid=user.uuid)
        response = client.get(
            path=path,
            content_type="application/json",
        )

        # Asserting that response data is correct
        assert response.status_code == DatabaseConnectionAPIError.status_code
        assert response.data["code"] == DatabaseConnectionAPIError.default_code
        assert (
            response.data["detail"] == DatabaseConnectionAPIError.default_detail
        )
