from apps.emails.applications.managers import ActionLinkManager
from apps.emails.domain.constants import SubjectsMail
from apps.emails.domain.typing import Token
from apps.emails.paths import TEMPLATES
from apps.users.domain.typing import UserUUID
from apps.users.models import BaseUser
from apps.utils.messages import ActivationErrors
from apps.api_exceptions import (
    AccountActivationAPIError,
    ResourceNotFoundAPIError,
)
from rest_framework.request import Request
from django.http.request import HttpRequest


class AccountActivation(ActionLinkManager):
    """
    This class encapsulates the logic of the use case responsible for sending the
    account activation message to a user's email, and the activation of his account.
    """

    subject = SubjectsMail.ACCOUNT_ACTIVATION.value
    email_body = TEMPLATES["account_management"]["activation"]["email_body"]
    action = "activar tu cuenta"

    def send_email(self, base_user: BaseUser | None, request: Request) -> None:

        if not base_user:
            raise ResourceNotFoundAPIError(
                code="user_not_found",
                detail=ActivationErrors.USER_NOT_FOUND.value,
            )
        elif base_user.is_active:
            raise AccountActivationAPIError(
                detail=ActivationErrors.ACTIVE_ACCOUNT.value
            )

        super().send_email(base_user=base_user, request=request)

    def check_token(
        self, token: Token, user_uuid: UserUUID, request: HttpRequest
    ) -> None:

        super().check_token(token=token, user_uuid=user_uuid, request=request)

        self.base_user.is_active = True
        self.base_user.save()
