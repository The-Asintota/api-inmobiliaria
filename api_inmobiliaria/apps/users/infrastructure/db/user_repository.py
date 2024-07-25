from apps.users.models import User, UserManager
from apps.exceptions import DatabaseConnectionError
from django.contrib.contenttypes.models import ContentType
from django.db import OperationalError
from django.db.models import QuerySet, Model
from typing import Dict, Any


class UserRepository:
    """
    UserRepository is a class that provides an abstraction of the database
    operations or queries related to a user.
    """

    __model = User

    @classmethod
    def create(cls, data: Dict[str, Any], role: str, is_active: bool) -> User:
        """
        Inserts a new user into the database.

        #### Parameters:
        - data: Dictionary containing the user's data.
        - role: Role of the user.
        - is_active: Boolean that indicates if the user is active or not.

        #### Raises:
        - DatabaseConnectionError: If there is an operational error with the
        database.
        """

        user_manager: UserManager = cls.__model.objects

        try:
            user = user_manager.create_user(
                base_data=data["base_data"],
                profile_data=data["profile_data"],
                related_model_name=role,
                is_active=is_active,
            )
        except OperationalError:
            # In the future, a retry system will be implemented when the database is
            # suddenly unavailable.
            raise DatabaseConnectionError()

        return user

    @classmethod
    def get(cls, **filters) -> QuerySet[User]:
        """
        Retrieves a user from the database according to the provided filters.

        #### Parameters:
        - filters: Keyword arguments that define the filters to apply.

        #### Raises:
        - DatabaseConnectionError: If there is an operational error with the
        database.
        """

        try:
            user_list = (
                cls.__model.objects.select_related("content_type")
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
            raise DatabaseConnectionError()

        return user_list

    @classmethod
    def get_role_data(
        cls, user: User = None, role: str = None, **filters
    ) -> QuerySet[Model]:
        """
        Retrieves the related data of a user role from the database according to
        the provided filters.

        #### Parameters:
        - user: User instance from which to retrieve the related data.
        - role: Role of the user from which to retrieve the related data.
        - filters: Keyword arguments that define the filters to apply.

        #### Raises:
        - DatabaseConnectionError: If there is an operational error with the
        database.
        - ValueError: If the 'user' or 'role' parameter is not provided.
        """

        if user:
            related_model = user.content_type.model_class()
        elif role:
            content_type = ContentType.objects.get(model=role)
            related_model = content_type.model_class()
        else:
            raise ValueError("The 'user' or 'role' parameter must be provided.")

        try:
            related_data = related_model.objects.filter(**filters)
        except OperationalError:
            # In the future, a retry system will be implemented when the database is
            # suddenly unavailable.
            raise DatabaseConnectionError()

        return related_data
