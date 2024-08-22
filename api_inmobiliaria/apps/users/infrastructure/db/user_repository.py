from apps.users.models import User, UserManager
from apps.api_exceptions import DatabaseConnectionAPIError
from django.contrib.contenttypes.models import ContentType
from django.db import OperationalError
from django.db.models import QuerySet, Model
from typing import Dict, Any, Optional


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
    def get_role_data(
        cls,
        user_base: Optional[User] = None,
        role: Optional[str] = None,
        **filters,
    ) -> QuerySet[Model]:
        """
        Retrieves the related data of a user role from the database according to
        the provided filters.

        #### Parameters:
        - user_base: An instance of the User model.
        - role: Role of the user from which to retrieve the related data.
        - filters: Keyword arguments that define the filters to apply.

        #### Raises:
        - DatabaseConnectionAPIError: If there is an operational error with the
        database.
        - ValueError: If the 'user' or 'role' parameter is not provided.
        """

        if user_base:
            related_model = user_base.content_type.model_class()
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
            raise DatabaseConnectionAPIError()

        return related_data
