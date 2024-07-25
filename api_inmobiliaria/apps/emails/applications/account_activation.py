from apps.emails.domain.abstractions import ITokenGenerator, ITokenRepository
from apps.emails.domain.typing import Token
from apps.emails.domain.constants import SubjectsMail, LOGIN_URL
from apps.emails.paths import TEMPLATES
from apps.emails.exceptions import AccountActivationError, TokenError
from apps.users.domain.abstractions import IUserRepository
from apps.users.domain.typing import UserUUID
from apps.users.models import User
from apps.exceptions import ResourceNotFoundError
from django.http.request import HttpRequest
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.sites.shortcuts import get_current_site
from typing import Any, Dict


class AccountActivation:
    """
    This class is responsible for sending an email to the user with a link to activate
    their account.
    """

    def __init__(
        self,
        user_repository: IUserRepository = None,
        token_repository: ITokenRepository = None,
        token_class: ITokenGenerator = None,
        smtp_class: EmailMessage = None,
    ) -> None:
        """
        Initializes the UserAccountActivation class.

        #### Parameters:
        - user_repository: An interface that provides an abstraction of database
        operations related to a user.
        - token_reposiroty: An interface that provides an abstraction of database
        operations related to a token.
        - token_class: An interface that provides an abstraction of the token
        generator.
        - smtp_class: An interface that provides an abstraction of the email message.
        """

        self._user_repository = user_repository
        self._token_repository = token_repository
        self._token_class = token_class
        self.smtp_class = smtp_class

    def _get_message_data(
        self, user: User, token: Token, request: HttpRequest
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
                        force_bytes(user.uuid)
                    ),
                    "token": token,
                },
            ),
            "to": [user.email],
        }

    def _compose_and_dispatch(
        self, user: User, token: Token, request: HttpRequest
    ) -> None:
        """
        Compose and send the message to the user's email.

        #### Parameters:
        - user: A instance of the User model.
        - token: This is a unique identifier that guarantees the security and validity
        of the initiated process.
        - request: An instance of the HttpRequest class.
        """

        email = self.smtp_class(
            **self._get_message_data(user=user, token=token, request=request)
        )
        email.content_subtype = "html"
        email.send()

    def send_email(self, user: User, request: HttpRequest) -> None:
        """
        Send the account activation message for a user.

        #### Parameters:
        - user: A instance of the User model.
        - request: An instance of the HttpRequest class.

        #### Raises:
        - AccountActivationError: The user is already active.
        """

        if user.is_active:
            raise AccountActivationError(
                detail={
                    "message": "No se puede activar la cuenta, ya que el usuario ya está activo. Te invitamos a iniciar sesión y disfrutar de nuestros servicios.",
                    "redirect": {
                        "action": "Iniciar sesión",
                        "url": LOGIN_URL,
                    },
                }
            )

        token = self._token_class.make_token(user=user)
        self._compose_and_dispatch(user=user, token=token, request=request)

    def check_token(self, token: Token, user_uuid: UserUUID) -> None:
        """
        Check the token and activate the user account.

        #### Parameters:
        - token: A unique identifier that guarantees the security and validity of the
        initiated process.
        - user_uuid: A unique identifier for the user.

        #### Raises:
        - TokenError: The token is invalid or expired.
        - ResourceNotFoundError: The user does not exist.
        """

        user = self._user_repository.get(uuid=user_uuid).first()

        if not user:
            raise ResourceNotFoundError(
                detail="El usuario que solícita confirmar su correoelectrónico no existe. Te invitamos a registrarte en nuestra plataforma para que puedas disfrutar de nuestros servicvios."
            )

        token_obj = self._token_repository.get(token=token).first()

        if token_obj.is_expired():
            raise TokenError(
                code="token_expired",
                detail="El enlace de activación de tu cuenta ha expirado. Te invitamos a solicitar un nuevo enlace.",
            )
        elif not self._token_class.check_token(user=user, token=token):
            raise TokenError(
                code="token_invalid",
                detail="El enlace de activación de tu cuenta ya ha sido utilizado. Te invitamos a iniciar sesión y disfrutar de nuestros servicios.",
            )

        user.is_active = True
        user.save()
