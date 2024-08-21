from rest_framework.permissions import BasePermission
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request


class IsJWTOwner(BasePermission):
    """
    Checks if the user making the request is the owner of the JWT.
    """

    message = "The user making the request is not the owner of the JWT."
    code = "permission_denied"

    def has_permission(self, request: Request, view: GenericAPIView) -> bool:
        access_payload = request.auth.payload

        return access_payload["user_uuid"] == view.kwargs["user_uuid"]
