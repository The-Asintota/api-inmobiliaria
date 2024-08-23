from apps.emails.infrastructure.db import TokenRepository
from apps.emails.applications import ActionLinkManager
from apps.users.infrastructure.db import UserRepository
from apps.utils.generators import TokenGenerator
from apps.utils.validators import is_valid_uuid
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework import status
from drf_spectacular.utils import extend_schema


@extend_schema(exclude=True)
class SendTokenAPIView(GenericAPIView):
    """
    API view for sending an account activation email to a user.

    This view handles requests to send an account activation email to the user. The
    email contains instructions and a link that allows the user to activate their
    account in the system. The user is identified by the UUID provided in the URL.
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    application_class = None
    action = None

    def get(self, request: Request, *args, **kwargs) -> Response:
        """
        Handle GET requests to send an account activation email to a user.

        This method sends an account activation email to the user with the specified
        UUID. The user is identified by the UUID in the URL.
        """

        if not is_valid_uuid(value=kwargs["user_uuid"]):
            return Response(
                data={
                    "code": "invalid_request_data",
                    "detail": "The user UUID provided is invalid.",
                },
                status=status.HTTP_400_BAD_REQUEST,
                content_type="application/json",
            )

        user = UserRepository.get_user_data(uuid=kwargs["user_uuid"]).first()

        application: ActionLinkManager = self.application_class(
            token_class=TokenGenerator(),
            token_repository=TokenRepository,
        )
        application.send_email(user=user, request=request)

        return Response(
            data={
                "detail": {
                    "message": f"Se ha enviado a tu dirección de correo electrónico un mensaje con instrucciones para {self.action}. Por favor, compruebe su bandeja de entrada."
                }
            },
            status=status.HTTP_200_OK,
            content_type="application/json",
        )
