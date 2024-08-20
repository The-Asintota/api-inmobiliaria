from apps.users.domain.abstractions import IUserRepository
from apps.users.models import User
from django.db.models import Model


class UserDataManager:
    """
    Manages user data operations.
    """

    def __init__(self, user_repository: IUserRepository) -> None:
        self._user_repository = user_repository

    def get(self, user_model: User) -> Model:
        """
        Retrieves the role data of a user.
        """

        role_data = self._user_repository.get_role_data(
            model_user=user_model, uuid=user_model.role_data_uuid
        ).first()

        return role_data
