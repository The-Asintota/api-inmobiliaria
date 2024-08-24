from apps.users.domain.constants import USER_ROLE_PERMISSIONS
from apps.users.domain.abstractions import IUserRepository
from apps.users.models import User
from apps.api_exceptions import PermissionDeniedAPIError
from django.db.models import Model


class UserDataManager:
    """
    Manages user data operations.
    """

    def __init__(self, user_repository: IUserRepository) -> None:
        self._user_repository = user_repository

    def get(self, user_base: User) -> Model:
        """
        Get the role data of a user.

        #### Parameters:
        - user_base: An instance of the User model.

        #### Raises:
        - PermissionDeniedAPIError: If the user does not have the required permissions.
        """

        role_user = user_base.content_type.model

        if not user_base.has_perm(
            perm=USER_ROLE_PERMISSIONS[role_user]["view_data"]
        ):
            raise PermissionDeniedAPIError()

        return self._user_repository.get_role_data(user_base=user_base).first()
