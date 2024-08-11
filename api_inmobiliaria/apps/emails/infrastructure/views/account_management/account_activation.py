from apps.emails.infrastructure.db import TokenRepository
from apps.emails.infrastructure.serializers import (
    Base64UserTokenSerializer,
)
from apps.emails.applications import AccountActivation, ActionLinkManagerErrors
from apps.emails.domain.constants import LOGIN_URL
from apps.emails.paths import TEMPLATES
from apps.emails.utils import TokenGenerator
from apps.users.infrastructure.db import UserRepository
from apps.api_exceptions import DatabaseConnectionAPIError
from apps.utils import view_exception_handler
from django.utils.decorators import method_decorator
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import render
from django.views.generic import View
from rest_framework import status


@method_decorator(view_exception_handler, name="dispatch")
class AccountActivationView(View):
    """
    View for validating a token sent to the user's email address. The token is used to
    activate the user's account.
    """

    application_class = AccountActivation
    serializer_class = Base64UserTokenSerializer
    path_send_mail = None

    @staticmethod
    def _handle_invalid_request(
        request: HttpRequest, status_code: int
    ) -> HttpResponse:
        """
        Handles invalid requests by rendering an error page.
        """

        return render(
            request=request,
            template_name=TEMPLATES["account_management"]["error"],
            context=ActionLinkManagerErrors.DEFAULT.value,
            status=status_code,
        )

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """
        Handles the GET request to check the validity of the token. The token is used
        to confirm the user's email address and activate their account.
        """

        serializer = self.serializer_class(data=kwargs)

        if not serializer.is_valid():
            return self._handle_invalid_request(
                request=request,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            self.application_class(
                user_repository=UserRepository,
                token_repository=TokenRepository,
                token_class=TokenGenerator(),
                path_send_mail=self.path_send_mail,
            ).check_token(
                request=request,
                token=serializer.validated_data["token"],
                user_uuid=serializer.validated_data["user_uuidb64"],
            )
        except DatabaseConnectionAPIError:
            return self._handle_invalid_request(
                request=request,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return render(
            request=request,
            template_name=TEMPLATES["account_management"]["activation"]["ok"],
            context={
                "redirect": {
                    "action": "Iniciar sesión",
                    "url": LOGIN_URL,
                }
            },
            status=status.HTTP_200_OK,
        )
