from apps.users.models import User, UserManager
from apps.api_exceptions import DatabaseConnectionAPIError
from django.contrib.contenttypes.models import ContentType
from django.db import OperationalError
from django.db.models import QuerySet, Model
from typing import Dict, Any


class UserRepository:
    """
    UserRepository is a class that provides an abstraction of the database
    operations or queries related to a user.
    """

    model = User

    @classmethod
    def create(cls, data: Dict[str, Any], role: str, is_active: bool) -> User:
        """
        Inserts a new user into the database.

        #### Parameters:
        - data: Dictionary containing the user's data.
        - role: Role of the user.
        - is_active: Boolean that indicates if the user is active or not.

        #### Raises:
        - DatabaseConnectionAPIError: If there is an operational error with the
        database.
        """

        user_manager: UserManager = cls.model.objects

        try:
            user = user_manager.create_user(
                base_data=data["base_data"],
                role_data=data["role_data"],
                related_model_name=role,
                is_active=is_active,
            )
        except OperationalError:
            # In the future, a retry system will be implemented when the database is
            # suddenly unavailable.
            raise DatabaseConnectionAPIError()

        return user

    @classmethod
    def get_user_data(cls, **filters) -> QuerySet[User]:
        """
        Retrieves a user from the database according to the provided filters.

        #### Parameters:
        - filters: Keyword arguments that define the filters to apply.

        #### Raises:
        - DatabaseConnectionAPIError: If there is an operational error with the
        database.
        """

        try:
            user_list = (
                cls.model.objects.select_related("content_type")
                .defer(
                    "password",
                    "last_login",
                    "is_superuser",
                    "is_staff",
                    "date_joined",
                )
                .filter(**filters)
            )
        except OperationalError:
            # In the future, a retry system will be implemented when the database is
            # suddenly unavailable.
            raise DatabaseConnectionAPIError()

        return user_list

    @classmethod
    def get_role_data(cls, user_base: User) -> Model:
        """
        Retrieves the role data of a user.

        #### Parameters:
        - user_base: An instance of the User model.

        #### Raises:
        - DatabaseConnectionAPIError: If there is an operational error with the
        database.
        """

        related_model = user_base.content_type.model_class()

        try:
            related_data = related_model.objects.filter(
                uuid=user_base.role_data_uuid
            ).first()
        except OperationalError:
            # In the future, a retry system will be implemented when the database is
            # suddenly unavailable.
            raise DatabaseConnectionAPIError()

        return related_data

    @classmethod
    def data_exists(cls, role_user: str, **filters) -> bool:
        """
        Checks if a user exists in the database.

        #### Parameters:
        - role_user: Role of the user.
        - filters: Keyword arguments that define the filters to apply.

        #### Raises:
        - DatabaseConnectionAPIError: If there is an operational error with the
        database.
        """

        try:
            content_type = ContentType.objects.get(model=role_user)
            related_model = content_type.model_class()

            user_exists = related_model.objects.filter(**filters).exists()
        except OperationalError:
            # In the future, a retry system will be implemented when the database is
            # suddenly unavailable.
            raise DatabaseConnectionAPIError()

        return user_exists

    @classmethod
    def update_role_data(
        cls,
        user_base: User,
        data: Dict[str, Any],
    ) -> Model:
        """
        Updates the role data for a user.

        #### Parameters:
        - user_base: An instance of the User model.
        - data: Dictionary containing the data to update.

        #### Raises:
        - DatabaseConnectionAPIError: If there is an operational error with the
        database.
        """

        role_data = cls.get_role_data(user_base=user_base).first()

        try:
            for field, value in data.items():
                setattr(role_data, field, value)
            role_data.save()
        except OperationalError:
            # In the future, a retry system will be implemented when the database is
            # suddenly unavailable.
            raise DatabaseConnectionAPIError()

        return role_data
