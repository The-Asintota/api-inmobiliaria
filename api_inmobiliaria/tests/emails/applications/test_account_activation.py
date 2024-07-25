from django.test import RequestFactory
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.sites.shortcuts import get_current_site
from apps.emails.applications import AccountActivation
from apps.emails.domain.constants import SubjectsMail
from apps.emails.paths import TEMPLATES
from apps.emails.exceptions import AccountActivationError
from apps.users.models import User
from unittest.mock import Mock
from uuid import uuid4
import pytest


class TestApplicationSendMail:
    """
    A test class for the `UserAccountActivation` application. This class contains test
    methods to verify the behavior of sending an email to activate a user account.
    """

    application_class = AccountActivation

    def test_send_success(self, token_generator: Mock) -> None:
        # Preparing the data
        user = User(
            uuid=uuid4(),
            email="user1@email.com",
            is_active=False,
        )
        request = RequestFactory().post("/")
        token_expected = "token1234"
        message_expected = {
            "subject": SubjectsMail.ACCOUNT_ACTIVATION.value,
            "body": render_to_string(
                template_name=TEMPLATES["account_activation"]["email_body"],
                context={
                    "email": user.email,
                    "domain": get_current_site(request),
                    "user_uuidb64": urlsafe_base64_encode(
                        force_bytes(user.uuid)
                    ),
                    "token": token_expected,
                },
            ),
            "to": [user.email],
        }

        # Preparing the mocks
        smtp_class = Mock()
        smtp_class_instance = Mock()
        token_generator_instance = Mock()

        # Mocking the methods
        make_token: Mock = token_generator_instance.make_token
        send: Mock = smtp_class_instance.send

        # Setting the return values
        smtp_class.return_value = smtp_class_instance
        token_generator.return_value = token_generator_instance
        make_token.return_value = token_expected

        # Instantiating the application and calling the method
        app = self.application_class(
            token_class=token_generator, smtp_class=smtp_class
        )
        app.send_email(user=user, request=request)

        # Asserting that the message is created with the correct data
        message_data = app._get_message_data(
            user=user, token=token_expected, request=request
        )
        assert message_data == message_expected
        send.assert_called_once()

    def test_if_user_already_active(self, token_generator: Mock) -> None:
        # Preparing the data
        user = User(
            uuid=uuid4(),
            email="user1@email.com",
            is_active=True,
        )
        request = RequestFactory().post("/")

        # Preparing the mocks
        smtp_class = Mock()
        smtp_class_instance = Mock()

        # Mocking the methods
        send: Mock = smtp_class_instance.send

        # Instantiating the application and calling the method
        with pytest.raises(AccountActivationError):
            self.application_class(
                token_class=token_generator, smtp_class=smtp_class
            ).send_email(user=user, request=request)

        # Asserting that the message is not sent
        send.assert_not_called()
