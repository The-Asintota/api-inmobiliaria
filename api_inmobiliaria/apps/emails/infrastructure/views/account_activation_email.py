from apps.emails.applications import AccountActivation
from apps.emails.utils import TokenGenerator
from apps.users.infrastructure.db import UserRepository
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from rest_framework import status
from drf_spectacular.utils import extend_schema


@extend_schema(exclude=True)
class AccountActivationEmailAPIView(GenericAPIView):
    """
    API view for sending an account activation email to a user.

    This view handles requests to send an account activation email to the user. The
    email contains instructions and a link that allows the user to activate their
    account in the system. The user is identified by the UUID provided in the URL.
    """

    authentication_classes = []
    permission_classes = []
    application_class = AccountActivation
    __user_repository = UserRepository

    def get(self, request: Request, *args, **kwargs) -> Response:
        """
        Handle GET requests to send an account activation email to a user.

        This method sends an account activation email to the user with the specified
        UUID. The user is identified by the UUID in the URL.
        """

        user = self.__user_repository.get_user_data(
            uuid=kwargs["user_uuid"]
        ).first()

        self.application_class(token_class=TokenGenerator()).send_email(
            user=user, request=request
        )

        return Response(
            data={
                "detail": {
                    "message": "Se ha enviado a tu dirección de correo electrónico un mensaje con el nuevo enlace de activación de tu cuenta. Por favor, compruebe su bandeja de entrada."
                }
            },
            status=status.HTTP_200_OK,
            content_type="application/json",
        )
