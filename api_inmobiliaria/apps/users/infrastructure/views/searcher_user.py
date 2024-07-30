from apps.users.infrastructure.serializers import (
    SearcherRegisterSerializer,
)
from apps.users.infrastructure.db import UserRepository
from apps.users.infrastructure.views.utils import MethodHTTPMapped
from apps.users.infrastructure.schemas.searcher_user import (
    SearcherUserRegisterMethodSchema,
)
from apps.users.applications import SearcherUsesCases
from rest_framework.serializers import Serializer
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status, generics
from typing import Dict, Any, List


class SearcherUserAPIView(MethodHTTPMapped, generics.GenericAPIView):
    """
    API view for managing operations for users with `searcher role`.

    It uses a mapping approach to determine the appropriate application logic,
    permissions, and serializers based on the HTTP method of the incoming request.
    """

    application_class = SearcherUsesCases(user_repository=UserRepository)
    application_mapping = {
        "POST": application_class.create_user,
    }
    authentication_mapping = {
        "POST": [],
    }
    permission_mapping = {
        "POST": [],
    }
    serializer_mapping = {
        "POST": SearcherRegisterSerializer,
    }
    status_code_mapping = {
        "POST": status.HTTP_201_CREATED,
    }

    def _handle_valid_request(
        self, data: Dict[str, Any], request: Request
    ) -> Response:
        application = self.get_application_class()
        application(data=data, request=request)

        return Response(status=self.get_status_code())

    @staticmethod
    def _handle_invalid_request(errors: List[Dict[str, Any]]) -> Response:

        return Response(
            data={
                "code": "invalid_request_data",
                "detail": errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
            content_type="application/json",
        )

    @SearcherUserRegisterMethodSchema
    def post(self, request: Request, *args, **kwargs) -> Response:
        """
        Handle POST requests for searcher user registration.

        This method allows the registration of a new seacher user, waiting for a
        POST request with the registration data. A successful registration will
        consist of saving the user's information in the database and sending a
        message to the user's email with a link that will allow them to activate
        their account.
        """

        serializer_class = self.get_serializer_class()
        serializer: Serializer = serializer_class(data=request.data)

        if serializer.is_valid():
            return self._handle_valid_request(
                data=serializer.validated_data, request=request
            )

        return self._handle_invalid_request(errors=serializer.errors)
