from apps.emails.applications.managers import ActionLinkManager
from apps.emails.domain.constants import SubjectsMail, LOGIN_URL, REGISTER_URL
from apps.emails.domain.typing import Token
from apps.emails.paths import TEMPLATES
from apps.users.domain.typing import UserUUID
from apps.users.models import User
from apps.api_exceptions import (
    AccountActivationAPIError,
    ResourceNotFoundAPIError,
)
from rest_framework.request import Request
from django.http.request import HttpRequest
from enum import Enum


class ActivationErrors(Enum):
    """
    Enum class for error messages related to the use case in charge of sending the
    account activation message. The errors that are in English are messages that the
    user will see.
    """

    USER_NOT_FOUND = {
        "message": "Ha ocurrido un error y no hemos podido identificarte. Por favor, regístrate en nuestra plataforma y activa tu cuenta para que puedas disfrutar de nuestros servicios.",
        "redirect": {
            "action": "Registrarse",
            "url": REGISTER_URL,
        },
    }
    ACTIVE_ACCOUNT = {
        "message": "¡Parece que tu cuenta ya estaba activada! Inicia sesión cuando quieras y comienza a disfrutar de nuestros servicios.",
        "redirect": {
            "action": "Iniciar sesión",
            "url": LOGIN_URL,
        },
    }


class AccountActivation(ActionLinkManager):
    """
    This class encapsulates the logic of the use case responsible for sending the
    account activation message to a user's email, and the activation of his account.
    """

    subject = SubjectsMail.ACCOUNT_ACTIVATION.value
    email_body = TEMPLATES["account_management"]["activation"]["email_body"]
    action = "activar tu cuenta"

    def send_email(self, user: User | None, request: Request) -> None:

        if not user:
            raise ResourceNotFoundAPIError(
                code="user_not_found",
                detail=ActivationErrors.USER_NOT_FOUND.value,
            )
        elif user.is_active:
            raise AccountActivationAPIError(
                detail=ActivationErrors.ACTIVE_ACCOUNT.value
            )

        super().send_email(user=user, request=request)

    def check_token(
        self, token: Token, user_uuid: UserUUID, request: HttpRequest
    ) -> None:

        super().check_token(token=token, user_uuid=user_uuid, request=request)

        self.user.is_active = True
        self.user.save()
