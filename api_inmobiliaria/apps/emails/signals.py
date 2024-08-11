from apps.emails.infrastructure.db import TokenRepository
from apps.emails.applications import AccountActivation
from apps.emails.utils import TokenGenerator
from apps.users.models import User
from apps.users.signals import account_activation_mail
from django.http.request import HttpRequest
from django.dispatch import receiver


@receiver(account_activation_mail)
def handle_send_activation_mail(
    sender, user: User, request: HttpRequest, **kwargs
) -> None:
    """
    This function is activated when a user-registered signal is sent. Generate an
    activation token and send an account activation email to the user.
    """

    application = AccountActivation(
        token_repository=TokenRepository,
        token_class=TokenGenerator(),
    )
    application.send_email(user=user, request=request)
