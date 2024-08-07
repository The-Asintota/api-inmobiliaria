from apps.emails.infrastructure.db import TokenRepository
from apps.emails.infrastructure.serializers import (
    AccountActivationDataSerializer,
)
from apps.emails.applications import AccountActivation
from apps.emails.domain.constants import REGISTER_URL, LOGIN_URL
from apps.emails.paths import TEMPLATES
from apps.emails.utils import TokenGenerator
from apps.users.infrastructure.db import UserRepository
from apps.utils import view_exception_handler
from rest_framework import status
from django.utils.decorators import method_decorator
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import render
from django.views.generic import View
from typing import Dict, Any


@method_decorator(view_exception_handler, name="dispatch")
class AccountActivationView(View):
    """
    View for validating a token sent to the user's email address. The token is used to
    activate the user's account.
    """

    application_class = AccountActivation
    serializer_class = AccountActivationDataSerializer

    @staticmethod
    def __handle_invalid_request(
        request: HttpRequest, context: Dict[str, Any]
    ) -> HttpResponse:
        """
        Handles invalid requests by rendering an error page.
        """

        return render(
            request=request,
            template_name=TEMPLATES["account_activation"]["failed"],
            context=context,
            status=status.HTTP_400_BAD_REQUEST,
        )

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """
        Handles the GET request to check the validity of the token. The token is used
        to confirm the user's email address and activate their account.
        """

        serializer = self.serializer_class(data=kwargs)

        if not serializer.is_valid():
            return self.__handle_invalid_request(
                request=request,
                context={
                    "message": "Algo ha ido mal. Vuelva a intentarlo más tarde.",
                    "redirect": {
                        "action": "Registrarse",
                        "url": REGISTER_URL,
                    },
                    "user_uuid": None,
                },
            )

        self.application_class(
            user_repository=UserRepository,
            token_repository=TokenRepository,
            token_class=TokenGenerator(),
        ).check_token(
            request=request,
            token=serializer.validated_data["token"],
            user_uuid=serializer.validated_data["user_uuidb64"],
        )

        return render(
            request=request,
            template_name=TEMPLATES["account_activation"]["success"],
            context={
                "redirect": {
                    "action": "Iniciar sesión",
                    "url": LOGIN_URL,
                }
            },
            status=status.HTTP_200_OK,
        )
