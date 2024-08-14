from apps.emails.infrastructure.db import TokenRepository
from apps.emails.applications import AccountActivation
from apps.emails.domain.constants import TOKEN_EXPIRATION
from apps.emails.models import Token
from apps.emails.utils import TokenGenerator
from apps.users.infrastructure.db import UserRepository
from apps.users.models import User
from apps.api_exceptions import (
    AccountActivationAPIError,
    ResourceNotFoundAPIError,
    DatabaseConnectionAPIError,
)
from apps.view_exceptions import ResourceNotFoundViewError, TokenViewError
from tests.factory import UserFactory
from tests.utils import empty_queryset
from django.test import RequestFactory
from django.core import mail
from unittest.mock import Mock
from datetime import timedelta
from uuid import uuid4
import pytest


@pytest.mark.django_db
class TestApplicationSendMail:
    """
    This class encapsulates the tests for the use case responsible for sending the
    account activation email.
    """

    application_class = AccountActivation
    user_factory = UserFactory

    def test_send_success(self) -> None:
        """
        This test is responsible for validating the expected behavior of the
        `send_email` method when the user data is valid.
        """

        # Creating the user data to be used in the test
        user, _ = self.user_factory.create_searcher_user(
            is_active=False, save=True, add_perm=False
        )

        # Instantiating the application and calling the method
        app = self.application_class(
            token_class=TokenGenerator(), token_repository=TokenRepository
        )
        app.send_email(user=user, request=RequestFactory().post("/"))

        # Asserting that the message is sent and the token is created
        assert len(mail.outbox) == 1
        assert Token.objects.count() == 1

    def test_is_user_not_found(self) -> None:
        """
        This test is responsible for validating the expected behavior of the
        `send_email` method when the user data is invalid.
        """

        # Instantiating the application and calling the method
        with pytest.raises(ResourceNotFoundAPIError):
            self.application_class(
                token_class=TokenGenerator(), token_repository=TokenRepository
            ).send_email(user=None, request=RequestFactory().post("/"))

        # Asserting that the message is not sent and the token is not created
        assert len(mail.outbox) == 0
        assert Token.objects.count() == 0

    def test_if_user_already_active(self) -> None:
        """
        This test is responsible for validating the expected behavior of the
        `send_email` method when the user account is already active.
        """

        # Instantiating the application and calling the method
        with pytest.raises(AccountActivationAPIError):
            self.application_class(
                token_class=TokenGenerator(), token_repository=TokenRepository
            ).send_email(
                user=User(
                    uuid=uuid4(),
                    email="user1@email.com",
                    is_active=True,
                ),
                request=RequestFactory().post("/"),
            )

        # Asserting that the message is not sent and the token is not created
        assert len(mail.outbox) == 0
        assert Token.objects.count() == 0

    def test_if_conection_db_failed(self, token_repository: Mock) -> None:
        """
        Test that validates the expected behavior of the view when the connection to
        the database fails.
        """

        # Mocking the methods
        create: Mock = token_repository.create
        create.side_effect = DatabaseConnectionAPIError

        # Instantiating the application and calling the method
        with pytest.raises(DatabaseConnectionAPIError):
            self.application_class(
                token_class=TokenGenerator(), token_repository=token_repository
            ).send_email(
                user=User(
                    uuid=uuid4(),
                    email="user1@email.com",
                    is_active=False,
                ),
                request=RequestFactory().post("/"),
            )

        # Asserting that the message is not sent and the token is not created
        assert len(mail.outbox) == 0
        assert Token.objects.count() == 0


@pytest.mark.django_db
class TestApplicationCheckToken:
    """
    This class encapsulates the tests for the use case responsible for checking the
    token and activating the user account.
    """

    application_class = AccountActivation
    user_factory = UserFactory

    def test_check_token_success(self) -> None:
        """
        This test is responsible for validating the expected behavior of the
        `check_token` method when the token is valid.
        """

        # Creating the user and token to be used in the test
        user, _ = self.user_factory.create_searcher_user(
            is_active=False, save=True, add_perm=False
        )
        token = TokenGenerator().make_token(user=user)
        Token.objects.create(token=token)

        # Instantiating the application and calling the method
        self.application_class(
            token_class=TokenGenerator(),
            user_repository=UserRepository,
            token_repository=TokenRepository,
            path_send_mail="send_activation_mail",
        ).check_token(
            token=token,
            user_uuid=user.uuid,
            request=RequestFactory().post("/"),
        )

        # Asserting that the user is active
        user = User.objects.get(uuid=user.uuid)

        assert user.is_active

    def test_if_user_not_found(self, user_repository: Mock) -> None:
        """
        This test is responsible for validating the expected behavior of the
        `check_token` method when the user is not found.
        """

        user = User(uuid=uuid4(), email="user@gmail.com", is_active=False)

        # Preparing the mocks
        get_user_data: Mock = user_repository.get_user_data
        get_user_data.return_value = empty_queryset(model=User)

        # Instantiating the application and calling the method
        with pytest.raises(ResourceNotFoundViewError):
            self.application_class(
                token_class=TokenGenerator(),
                user_repository=user_repository,
                token_repository=TokenRepository,
                path_send_mail="send_activation_mail",
            ).check_token(
                token="token1234",
                user_uuid=user.uuid,
                request=RequestFactory().post("/"),
            )

    def test_if_token_expired(self) -> None:
        """
        This test is responsible for validating the expected behavior of the
        `check_token` method when the token is expired.
        """

        # Creating the user and token to be used in the test
        user, _ = self.user_factory.create_searcher_user(
            is_active=False, save=True, add_perm=False
        )
        token = TokenGenerator().make_token(user=user)
        token_obj = Token.objects.create(token=token)

        # Changing the token expiration date
        token_obj.date_joined -= timedelta(minutes=1) + TOKEN_EXPIRATION
        token_obj.save()

        # Instantiating the application and calling the method
        with pytest.raises(TokenViewError):
            self.application_class(
                token_class=TokenGenerator(),
                user_repository=UserRepository,
                token_repository=TokenRepository,
                path_send_mail="send_activation_mail",
            ).check_token(
                token=token,
                user_uuid=user.uuid,
                request=RequestFactory().post("/"),
            )

        # Asserting that the user is not active
        user = User.objects.get(uuid=user.uuid)

        assert not user.is_active

    def test_if_token_invalid(self) -> None:
        """
        This test is responsible for validating the expected behavior of the
        `check_token` method when the token is invalid.
        """

        # Creating the user and token to be used in the test
        user_1, _ = self.user_factory.create_searcher_user(
            is_active=False, save=True, add_perm=False
        )
        user_2, _ = self.user_factory.create_searcher_user(
            is_active=False, save=True, add_perm=False
        )
        token = TokenGenerator().make_token(user=user_2)
        Token.objects.create(token=token)

        # Instantiating the application and calling the method
        with pytest.raises(TokenViewError):
            self.application_class(
                token_class=TokenGenerator(),
                user_repository=UserRepository,
                token_repository=TokenRepository,
                path_send_mail="send_activation_mail",
            ).check_token(
                token=token,
                user_uuid=user_1.uuid,
                request=RequestFactory().post("/"),
            )

        # Asserting that the user is not active
        user = User.objects.get(uuid=user_1.uuid)

        assert not user.is_active

    def test_if_conection_db_failed(
        self, user_repository: Mock, token_repository: Mock
    ) -> None:
        """
        Test that validates the expected behavior of the view when the connection to
        the database fails.
        """

        # Creating the user to be used in the test
        user, _ = self.user_factory.create_searcher_user(
            is_active=False, save=True, add_perm=False
        )

        # Mocking the methods
        get: Mock = token_repository.get
        get.side_effect = DatabaseConnectionAPIError
        get_user_data: Mock = user_repository.get_user_data
        get_user_data.side_effect = DatabaseConnectionAPIError

        for ur, tr in [
            (user_repository, TokenRepository),
            (UserRepository, token_repository),
        ]:
            # Instantiating the application and calling the method
            with pytest.raises(DatabaseConnectionAPIError):
                self.application_class(
                    token_class=TokenGenerator(),
                    user_repository=ur,
                    token_repository=tr,
                    path_send_mail="send_activation_mail",
                ).check_token(
                    token="token123",
                    user_uuid=user.uuid,
                    request=RequestFactory().post("/"),
                )

            # Asserting that the user is not active
            user = User.objects.get(uuid=user.uuid)

            assert not user.is_active
