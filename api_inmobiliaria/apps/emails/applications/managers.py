from apps.emails.domain.abstractions import ITokenGenerator, ITokenRepository
from apps.emails.domain.typing import Token
from apps.emails.paths import TEMPLATES
from apps.users.domain.abstractions import IUserRepository
from apps.users.domain.typing import UserUUID
from apps.users.models import BaseUser
from apps.utils.messages import ActionLinkManagerErrors
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
        self.base_user = None

    def _get_message_data(
        self, base_user: BaseUser, token: Token, request: Request
    ) -> Dict[str, Any]:
        """
        Constructs and returns a dictionary containing the subject, body, and
        recipient of the message.

        The email body is rendered from a predefined template with context variables
        including the user's email, the current site domain, a base64 encoded user id,
        and a unique token.

        #### Parameters:
        - base_user: An instance of the BaseUser model.
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
                    "email": base_user.email,
                    "domain": get_current_site(request),
                    "user_uuidb64": urlsafe_base64_encode(
                        s=force_bytes(s=base_user.uuid)
                    ),
                    "token": token,
                },
            ),
            "to": [base_user.email],
        }

    def _compose_and_dispatch(
        self, base_user: BaseUser, token: Token, request: Request
    ) -> None:
        """
        Compose and send the message to the user's email.

        #### Parameters:
        - base_user: A instance of the BaseUser model.
        - token: This is a unique identifier that guarantees the security and validity
        of the initiated process.
        - request: This object comes from the view and contains the request
        information.
        """

        email = EmailMessage(
            **self._get_message_data(
                base_user=base_user, token=token, request=request
            )
        )
        email.content_subtype = "html"
        email.send()

    def send_email(self, base_user: BaseUser | None, request: Request) -> None:
        """
        Send the message to the email of the indicated user.

        This method should only be used within the execution flow of a `APIview`, as it
        involves rendering templates.

        #### Parameters:
        - base_user: An instance of the BaseUser model.
        - request: This object comes from the view and contains the request
        information.
        """

        token = self._token_class.make_token(base_user=base_user)
        self._token_repository.create(token=token)
        self._compose_and_dispatch(
            base_user=base_user, token=token, request=request
        )

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

        self.base_user = self._user_repository.get_base_data(uuid=user_uuid)

        if not self.base_user:
            raise ResourceNotFoundViewError(
                request=request,
                template_name=TEMPLATES["account_management"]["error"],
                context=ActionLinkManagerErrors.USER_NOT_FOUND.value,
            )

        token_obj = self._token_repository.get(token=token)

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
        elif not self._token_class.check_token(
            user=self.base_user, token=token
        ):
            raise TokenViewError(
                request=request,
                context=ActionLinkManagerErrors.TOKEN_INVALID.value,
                template_name=TEMPLATES["account_management"]["error"],
            )
