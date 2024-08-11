from apps.emails.domain.abstractions import ITokenGenerator, ITokenRepository
from apps.emails.domain.constants import LOGIN_URL, REGISTER_URL, HOME_URL
from apps.emails.domain.typing import Token
from apps.emails.paths import TEMPLATES
from apps.users.domain.abstractions import IUserRepository
from apps.users.domain.typing import UserUUID
from apps.users.models import User
from apps.view_exceptions import (
    ResourceNotFoundViewError,
    TokenViewError,
)
from rest_framework.request import Request
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import EmailMessage
from django.http.request import HttpRequest
from django.urls import reverse
from typing import Any, Dict
from enum import Enum


class ActionLinkManagerErrors(Enum):
    """
    Error enumeration for the email communication module related to user account
    management.
    """

    DEFAULT = {
        "message": "Lo sentimos, se ha producido un error inesperado en nuestro sistema. No se ha podido completar tu solicitud en este momento. Por favor, inténtalo de nuevo más tarde. Si el problema persiste, puedes ponerte en contacto con nuestro equipo de soporte al cliente para obtener más ayuda. Disculpa las molestias y gracias por tu paciencia.",
        "redirect": {
            "action": "Ir al inicio",
            "url": HOME_URL,
        },
    }
    USER_NOT_FOUND = {
        "message": "Ha ocurrido un error y no hemos podido identificarte. Por favor, regístrate en nuestra plataforma para disfrutar de nuestros servicios.",
        "redirect": {
            "action": "Registrarse",
            "url": REGISTER_URL,
        },
    }
    TOKEN_EXPIRED = {
        "message": "El enlace ha expirado. Para tu seguridad, estos enlaces son válidos solo por un tiempo limitado. Por favor, solicita un nuevo enlace para {action}",
        "redirect": {
            "action": "Solicitar nuevo enlace",
        },
    }
    TOKEN_INVALID = {
        "message": "Lo sentimos, este enlace es de un solo uso y ya ha sido utilizado. Para acceder a nuestros servicios o realizar otras acciones, por favor inicia sesión en tu cuenta.",
        "redirect": {
            "action": "Iniciar sesión",
            "url": LOGIN_URL,
        },
    }


class ActionLinkManager:
    """
    This class encapsulates the logic in charge of e-mail communication related to user
    account management.
    """

    subject: str
    email_body: str
    action: str

    def __init__(
        self,
        path_send_mail: str = None,
        user_repository: IUserRepository = None,
        token_repository: ITokenRepository = None,
        token_class: ITokenGenerator = None,
    ) -> None:
        self._user_repository = user_repository
        self._token_repository = token_repository
        self._token_class = token_class
        self.path_send_mail = path_send_mail
        self.user = None

    def _get_message_data(
        self, user: User, token: Token, request: Request
    ) -> Dict[str, Any]:
        """
        Constructs and returns a dictionary containing the subject, body, and
        recipient of the message.

        The email body is rendered from a predefined template with context variables
        including the user's email, the current site domain, a base64 encoded user id,
        and a unique token.

        #### Parameters:
        - user: An instance of the User model.
        - token: A unique identifier that guarantees the security and validity of the
        initiated process.
        - request: This object comes from the view and contains the request
        information.
        """

        return {
            "subject": self.subject,
            "body": render_to_string(
                template_name=self.email_body,
                context={
                    "email": user.email,
                    "domain": get_current_site(request),
                    "user_uuidb64": urlsafe_base64_encode(
                        s=force_bytes(s=user.uuid)
                    ),
                    "token": token,
                },
            ),
            "to": [user.email],
        }

    def _compose_and_dispatch(
        self, user: User, token: Token, request: Request
    ) -> None:
        """
        Compose and send the message to the user's email.

        #### Parameters:
        - user: A instance of the User model.
        - token: This is a unique identifier that guarantees the security and validity
        of the initiated process.
        - request: This object comes from the view and contains the request
        information.
        """

        email = EmailMessage(
            **self._get_message_data(user=user, token=token, request=request)
        )
        email.content_subtype = "html"
        email.send()

    def send_email(self, user: User | None, request: Request) -> None:
        """
        Send the message to the email of the indicated user.

        This method should only be used within the execution flow of a `APIview`, as it
        involves rendering templates.

        #### Parameters:
        - user: An instance of the User model.
        - request: This object comes from the view and contains the request
        information.
        """

        token = self._token_class.make_token(user=user)
        self._token_repository.create(token=token)
        self._compose_and_dispatch(user=user, token=token, request=request)

    def check_token(
        self, token: Token, user_uuid: UserUUID, request: HttpRequest
    ) -> None:
        """
        Verify the token provided.

        This method should only be used within the execution flow of a `View`, as
        it involves rendering templates.

        #### Parameters:
        - token: A unique identifier that guarantees the security and validity of the
        initiated process.
        - user_uuid: A unique identifier for the user.
        - request: This object comes from the view and contains the request
        information.

        #### Raises:
        - TokenViewError: The token is invalid or expired.
        - ResourceNotFoundViewError: The user does not exist.
        """

        self.user = self._user_repository.get_user_data(uuid=user_uuid).first()

        if not self.user:
            raise ResourceNotFoundViewError(
                request=request,
                template_name=TEMPLATES["account_management"]["error"],
                context=ActionLinkManagerErrors.USER_NOT_FOUND.value,
            )

        token_obj = self._token_repository.get(token=token).first()

        if not token_obj:
            raise ResourceNotFoundViewError(
                request=request,
                template_name=TEMPLATES["account_management"]["error"],
                context=ActionLinkManagerErrors.DEFAULT.value,
            )
        elif token_obj.is_expired():
            context = ActionLinkManagerErrors.TOKEN_EXPIRED.value
            context["redirect"]["url"] = reverse(
                viewname=self.path_send_mail,
                kwargs={"user_uuid": user_uuid},
            )
            context["message"] = context["message"].format(action=self.action)

            raise TokenViewError(
                request=request,
                context=context,
                template_name=TEMPLATES["account_management"]["error"],
            )
        elif not self._token_class.check_token(user=self.user, token=token):
            raise TokenViewError(
                request=request,
                context=ActionLinkManagerErrors.TOKEN_INVALID.value,
                template_name=TEMPLATES["account_management"]["error"],
            )
