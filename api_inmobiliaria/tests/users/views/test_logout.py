from apps.users.infrastructure.serializers import JWTSerializerErrorMessages
from apps.users.applications import JWTErrorMessages
from apps.users.domain.constants import UserRoles
from apps.users.models import User, JWT
from apps.api_exceptions import (
    DatabaseConnectionAPIError,
    ResourceNotFoundAPIError,
    JWTAPIError,
)
from tests.factory import JWTFactory
from tests.utils import empty_queryset
from rest_framework.fields import CharField
from django.test import Client
from django.urls import reverse
from unittest.mock import Mock, patch
from typing import Callable, Tuple, Dict, List, Any
import pytest


# This constant is used when the serializer error messages are the default.
DEFAULT_ERROR_MESSAGES = CharField().error_messages


@pytest.fixture
def setUp() -> Tuple[Client, str]:
    """
    A fixture to set up the client and the path for the view.
    """

    return Client(), reverse(viewname="jwt_logout_user")


class TestAPIView:
    """
    This class encapsulates all the tests of the view in charge of handling logout
    requests from a user.
    """

    @pytest.mark.django_db
    def test_request_valid(
        self,
        setUp: Tuple[Client, str],
        create_user: Callable[[bool, str, bool], Tuple[User, Dict[str, Dict]]],
        save_jwt_db: Callable[[User, Dict[str, Any]], JWT],
    ) -> None:
        """
        This test is responsible for validating the expected behavior of the view
        when the request data is valid.
        """

        # Creating a user
        user, _ = create_user(
            active=True, role=UserRoles.SEARCHER.value, add_perm=False
        )

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
    def test_request_invalid(
        self,
        setUp: Tuple[Client, str],
        data: Dict[str, str],
        error_messages: Dict[str, List],
    ) -> None:
        """
        This test is responsible for validating the expected behavior of the view
        when the request data is invalid.
        """

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
        self,
        setUp: Tuple[Client, str],
        create_user: Callable[[bool, str, bool], Tuple[User, Dict[str, Dict]]],
    ) -> None:
        """
        This test is responsible for validating the expected behavior of the view
        when the JWTs are not found in the database.
        """

        # Creating a user
        user, _ = create_user(
            active=True, role=UserRoles.SEARCHER.value, add_perm=False
        )

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
        assert response.status_code == ResourceNotFoundAPIError.status_code
        assert (
            response.data["code"] == JWTErrorMessages.TOKEN_NOT_FOUND_CODE.value
        )
        assert response.data["detail"] == JWTErrorMessages.TOKEN_NOT_FOUND.value

    @pytest.mark.django_db
    def test_if_jwt_not_match_user(
        self,
        setUp: Tuple[Client, str],
        create_user: Callable[[bool, str, bool], Tuple[User, Dict[str, Dict]]],
        save_jwt_db: Callable[[User, Dict[str, Any]], JWT],
    ) -> None:
        """
        This test is responsible for validating the expected behavior of the view
        when the JWTs do not match the user.
        """

        # Creating a user
        user, _ = create_user(
            active=True, role=UserRoles.SEARCHER.value, add_perm=False
        )

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
        assert response.status_code == JWTAPIError.status_code
        assert response.data["code"] == JWTAPIError.default_code
        assert response.data["detail"] == JWTErrorMessages.JWT_ERROR.value

    @patch("apps.users.infrastructure.views.jwt.UserRepository")
    def test_if_user_not_found(
        self, user_repository_mock: Mock, setUp: Tuple[Client, str]
    ) -> None:
        """
        This test is responsible for validating the expected behavior of the view
        when the user is not found in the database.
        """

        # Mocking the methods
        get_user_data: Mock = user_repository_mock.get_user_data

        # Setting the return values
        get_user_data.return_value = empty_queryset(model=User)

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
        assert response.status_code == ResourceNotFoundAPIError.status_code
        assert (
            response.data["code"] == JWTErrorMessages.USER_NOT_FOUND_CODE.value
        )
        assert response.data["detail"] == JWTErrorMessages.USER_NOT_FOUND.value

    @patch("apps.users.infrastructure.views.jwt.UserRepository")
    def test_exception_raised_db(
        self, user_repository_mock: Mock, setUp: Tuple[Client, str]
    ) -> None:
        """
        Test to check if the response is correct when an exception is raised.
        """

        # Mocking the methods
        get_user_data: Mock = user_repository_mock.get_user_data

        # Setting the return values
        get_user_data.side_effect = DatabaseConnectionAPIError

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
        assert response.status_code == DatabaseConnectionAPIError.status_code
        assert response.data["code"] == DatabaseConnectionAPIError.default_code
        assert (
            response.data["detail"] == DatabaseConnectionAPIError.default_detail
        )
