from apps.emails.domain.abstractions import ITokenGenerator, ITokenRepository
from apps.emails.domain.constants import SubjectsMail, LOGIN_URL, REGISTER_URL
from apps.emails.domain.typing import Token
from apps.emails.paths import TEMPLATES
from apps.users.domain.abstractions import IUserRepository
from apps.users.domain.typing import UserUUID
from apps.users.models import User
from apps.api_exceptions import (
    AccountActivationAPIError,
    ResourceNotFoundAPIError,
)
from apps.view_exceptions import (
    ResourceNotFoundViewError,
    TokenViewError,
)
from rest_framework.request import Request
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.http.response import HttpResponse
from django.http.request import HttpRequest
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse
from typing import Any, Dict
from enum import Enum


class ActivationErrors(Enum):
    """
    Enum class for error messages related to the use case in charge of sending the
    account activation message. The errors that are in English are messages that the
    user will see.
    """

    USER_NOT_FOUND_CODE = "user_not_found"
    USER_NOT_FOUND = {
        "message": "Ha ocurrido un error y no hemos podido identificarte. Por favor, regístrate en nuestra plataforma para disfrutar de nuestros servicios.",
        "redirect": {
            "action": "Registrarse",
            "url": REGISTER_URL,
        },
    }
    ACTIVE_ACCOUNT = {
        "message": "Tu cuenta ya ha sido activada. Por favor, inicia sesión para disfrutar de nuestros servicios.",
        "redirect": {
            "action": "Iniciar sesión",
            "url": LOGIN_URL,
        },
    }
    TOKEN_EXPIRED = {
        "message": "El enlace de activación de tu cuenta ha expirado. Por favor, solicita un nuevo enlace para activar tu cuenta.",
        "redirect": {
            "action": "Solicitar nuevo enlace",
        },
    }
    TOKEN_INVALID = {
        "message": "El enlace de activación de tu cuenta ya ha sido utilizado. Por favor, inicia sesión para disfrutar de nuestros servicios.",
        "redirect": {
            "action": "Iniciar sesión",
            "url": LOGIN_URL,
        },
    }


class AccountActivation:
    """
    This class encapsulates the logic of the use case responsible for sending the
    account activation message to a user's email, and the activation of his account.
    """

    def __init__(
        self,
        user_repository: IUserRepository = None,
        token_repository: ITokenRepository = None,
        token_class: ITokenGenerator = None,
    ) -> None:
        self.__user_repository = user_repository
        self.__token_repository = token_repository
        self.__token_class = token_class

    def __get_message_data(
        self, user: User, token: Token, request: Request
    ) -> Dict[str, Any]:
        """
        Constructs and returns a dictionary containing the subject, body, and
        recipient of the message for account activation.

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
            "subject": SubjectsMail.ACCOUNT_ACTIVATION.value,
            "body": render_to_string(
                template_name=TEMPLATES["account_activation"]["email_body"],
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

    def __compose_and_dispatch(
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
            **self.__get_message_data(user=user, token=token, request=request)
        )
        email.content_subtype = "html"
        email.send()

    def send_email(self, user: User | None, request: Request) -> None:
        """
        Send the account activation message for a user.

        #### Parameters:
        - user: An instance of the User model.
        - request: This object comes from the view and contains the request
        information.

        #### Raises:
        - AccountActivationAPIError: The user account is already active.
        - ResourceNotFoundAPIError: The user does not exist.
        """

        if not user:
            raise ResourceNotFoundAPIError(
                code=ActivationErrors.USER_NOT_FOUND_CODE.value,
                detail=ActivationErrors.USER_NOT_FOUND.value,
            )
        elif user.is_active:
            raise AccountActivationAPIError(
                detail=ActivationErrors.ACTIVE_ACCOUNT.value
            )

        token = self.__token_class.make_token(user=user)
        self.__compose_and_dispatch(user=user, token=token, request=request)

    def check_token(
        self, token: Token, user_uuid: UserUUID, request: HttpRequest
    ) -> HttpResponse:
        """
        Check the token and activate the user account.

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

        user = self.__user_repository.get_user_data(uuid=user_uuid).first()

        if not user:
            raise ResourceNotFoundViewError(
                request=request,
                template_name=TEMPLATES["account_activation"]["failed"],
                context=ActivationErrors.USER_NOT_FOUND.value,
            )

        token_obj = self.__token_repository.get(token=token).first()

        if token_obj.is_expired():
            context = ActivationErrors.TOKEN_EXPIRED.value
            context["redirect"]["url"] = reverse(
                viewname="account_activation_email",
                kwargs={"user_uuid": user_uuid},
            )

            raise TokenViewError(
                request=request,
                context=context,
                template_name=TEMPLATES["account_activation"]["failed"],
            )
        elif not self.__token_class.check_token(user=user, token=token):
            raise TokenViewError(
                request=request,
                context=ActivationErrors.TOKEN_INVALID.value,
                template_name=TEMPLATES["account_activation"]["failed"],
            )

        user.is_active = True
        user.save()
