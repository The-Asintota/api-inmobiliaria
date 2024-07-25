from apps.users.models import User, UserRoles
from apps.exceptions import DatabaseConnectionError
from tests.users.factory import JWTFactory
from tests.utils import empty_queryset
from django.test import Client
from django.urls import reverse
from unittest.mock import Mock, patch
from typing import Tuple, Dict, List
import pytest


@pytest.fixture
def setUp() -> Tuple[Client, str]:

    return Client(), reverse(viewname="logout_user")


class TestAPIView:
    """
    A test class for the `LogoutAPIView` view. This class contains test
    methods to verify the behavior of the view for logout user.
    """

    @pytest.mark.django_db
    def test_request_valid(
        self, setUp: Tuple[Client, str], save_user_db, save_jwt_db
    ) -> None:
        # Creating a user
        user, _ = save_user_db(active=True, role=UserRoles.SEARCHER.value)

        # Creating the token
        refresh_data = JWTFactory.refresh(
            user_uuid=user.uuid.__str__(), exp=False
        )
        access_data = JWTFactory.access(
            user_uuid=user.uuid.__str__(), exp=False
        )
        _ = save_jwt_db(user=user, data=access_data)
        _ = save_jwt_db(user=user, data=refresh_data)

        # Simulating the request
        client, path = setUp
        response = client.post(
            path=path,
            data={
                "refresh": refresh_data["token"],
                "access": access_data["token"],
            },
            content_type="application/json",
        )

        # Asserting that response data is correct
        assert response.status_code == 200

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        argnames="data, error_messages",
        argvalues=[
            (
                {},
                {
                    "refresh": ["This field is required."],
                    "access": ["This field is required."],
                },
            ),
            (
                {
                    "refresh": JWTFactory.refresh_invalid(),
                    "access": JWTFactory.access_invalid(),
                },
                {
                    "refresh": ["Token is invalid."],
                    "access": ["Token is invalid."],
                },
            ),
            (
                {
                    "refresh": JWTFactory.refresh(exp=True).get("token"),
                },
                {
                    "access": ["This field is required."],
                    "refresh": ["Token is expired."],
                },
            ),
        ],
        ids=[
            "empty_data",
            "tokens_invalid",
            "refresh_expired",
        ],
    )
    def test_request_invalid(
        self,
        setUp: Tuple[Client, str],
        data: Dict[str, str],
        error_messages: Dict[str, List],
    ) -> None:
        # Simulating the request
        client, path = setUp
        response = client.post(
            path=path,
            data=data,
            content_type="application/json",
        )

        # Asserting that response data is correct
        assert response.status_code == 400
        assert response.data["code"] == "invalid_request_data"

        # Asserting that the error messages are correct
        response_errors_formated = {
            field: [str(error) for error in errors]
            for field, errors in response.data["detail"].items()
        }

        for field, message in error_messages.items():
            assert response_errors_formated[field] == message

    @pytest.mark.django_db
    def test_if_jwt_not_found(
        self, setUp: Tuple[Client, str], save_user_db
    ) -> None:
        # Creating a user
        user, _ = save_user_db(active=True, role=UserRoles.SEARCHER.value)

        # Creating the token
        refresh = JWTFactory.refresh(
            user_uuid=user.uuid.__str__(), exp=False
        ).get("token")
        access = JWTFactory.access(
            user_uuid=user.uuid.__str__(), exp=False
        ).get("token")

        # Simulating the request
        client, path = setUp
        response = client.post(
            path=path,
            data={"refresh": refresh, "access": access},
            content_type="application/json",
        )

        # Asserting that response data is correct
        assert response.status_code == 404
        assert response.data["code"] == "token_not_found"
        assert response.data["detail"] == "JSON Web Tokens not found."

    @pytest.mark.django_db
    def test_if_jwt_not_match_user(
        self, setUp: Tuple[Client, str], save_user_db, save_jwt_db
    ) -> None:
        # Creating a user
        user, _ = save_user_db(active=True, role=UserRoles.SEARCHER.value)

        # Creating the token
        refresh_data = JWTFactory.refresh(
            user_uuid=user.uuid.__str__(), exp=False
        )
        access_data = JWTFactory.access(
            user_uuid=user.uuid.__str__(), exp=False
        )
        _ = save_jwt_db(user=user, data=access_data)
        _ = save_jwt_db(user=user, data=refresh_data)

        # Simulating the request
        client, path = setUp

        refresh = JWTFactory.refresh(
            user_uuid=user.uuid.__str__(), exp=False
        ).get("token")
        access = JWTFactory.access(
            user_uuid=user.uuid.__str__(), exp=False
        ).get("token")

        response = client.post(
            path=path,
            data={"refresh": refresh, "access": access},
            content_type="application/json",
        )

        # Asserting that response data is correct
        assert response.status_code == 401
        assert response.data["code"] == "token_error"
        assert (
            response.data["detail"]
            == "The JSON Web Tokens does not match the user's last tokens."
        )

    @patch("apps.users.infrastructure.views.jwt.UserRepository")
    def test_if_user_not_found(
        self, user_repository_mock: Mock, setUp: Tuple[Client, str]
    ) -> None:
        # Mocking the methods
        get_user: Mock = user_repository_mock.get

        # Setting the return values
        get_user.return_value = empty_queryset(model=User)

        # Simulating the request
        client, path = setUp

        refresh = JWTFactory.refresh(user_uuid="123", exp=False).get("token")
        access = JWTFactory.access(user_uuid="123", exp=False).get("token")

        response = client.post(
            path=path,
            data={"refresh": refresh, "access": access},
            content_type="application/json",
        )

        # Asserting that response data is correct
        assert response.status_code == 404
        assert response.data["code"] == "user_not_found"
        assert (
            response.data["detail"] == "The JSON Web Token user does not exist."
        )

    @patch("apps.users.infrastructure.views.jwt.UserRepository")
    def test_exception_raised_db(
        self, user_repository_mock: Mock, setUp: Tuple[Client, str]
    ) -> None:
        # Mocking the methods
        get: Mock = user_repository_mock.get

        # Setting the return values
        get.side_effect = DatabaseConnectionError

        # Simulating the request
        client, path = setUp
        response = client.post(
            path=path,
            data=JWTFactory.access_and_refresh(
                exp_access=False, exp_refresh=False
            ).get("tokens"),
            content_type="application/json",
        )

        # Asserting that response data is correct
        assert response.status_code == 500
        assert response.data["code"] == "database_connection_error"
        assert (
            response.data["detail"]
            == "Unable to establish a connection with the database. Please try again later."
        )
