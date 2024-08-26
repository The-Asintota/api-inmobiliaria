from apps.emails.infrastructure.db import TokenRepository
from apps.emails.applications.account_management import AccountActivation
from apps.users.models import BaseUser
from apps.users.signals import account_activation_mail
from apps.utils.generators import TokenGenerator
from django.http.request import HttpRequest
from django.dispatch import receiver


@receiver(account_activation_mail)
def handle_send_activation_mail(
    sender, base_user: BaseUser, request: HttpRequest, **kwargs
) -> None:
    """
    This function is activated when a user-registered signal is sent. Generate an
    activation token and send an account activation email to the user.

    #### Parameters:
    - sender: The sender of the signal.
    - base_user: The user to whom the activation email will be sent.
    - request: The request object that triggered the signal.
    """

    account_activation = AccountActivation(
        token_repository=TokenRepository,
        token_class=TokenGenerator(),
    )
    account_activation.send_email(base_user=base_user, request=request)
