from apps.users.models import BaseUser, UserManager
from apps.api_exceptions import DatabaseConnectionAPIError
from django.contrib.contenttypes.models import ContentType
from django.db import OperationalError
from django.db.models import Model
from typing import Dict, Any


class UserRepository:
    """
    UserRepository is a class that provides an abstraction of the database
    operations or queries related to a user.
    """

    model = BaseUser

    @classmethod
    def create(
        cls, data: Dict[str, Any], user_role: str, active: bool
    ) -> BaseUser:
        """
        Inserts a new user into the database.

        #### Parameters:
        - data: Dictionary containing the user's data.
        - user_role: Role of the user.
        - active: Boolean that indicates if the user is active or not.

        #### Raises:
        - DatabaseConnectionAPIError: If there is an operational error with the
        database.
        """

        user_manager: UserManager = cls.model.objects

        try:
            base_user = user_manager.create_user(
                base_data=data["base_data"],
                role_data=data["role_data"],
                related_model_name=user_role,
                is_active=active,
            )
        except OperationalError:
            # In the future, a retry system will be implemented when the database is
            # suddenly unavailable.
            raise DatabaseConnectionAPIError()

        return base_user

    @classmethod
    def get_base_data(cls, **filters) -> BaseUser | None:
        """
        Retrieves a user base data from the database based on the provided filters.

        #### Parameters:
        - filters: Keyword arguments that define the filters to apply.

        #### Raises:
        - DatabaseConnectionAPIError: If there is an operational error with the
        database.
        """

        try:
            base_user = (
                cls.model.objects.select_related("content_type")
                .defer(
                    "password",
                    "last_login",
                    "is_superuser",
                    "is_staff",
                    "date_joined",
                )
                .filter(**filters)
                .first()
            )
        except OperationalError:
            # In the future, a retry system will be implemented when the database is
            # suddenly unavailable.
            raise DatabaseConnectionAPIError()

        return base_user

    @classmethod
    def get_role_data(cls, base_user: BaseUser) -> Model:
        """
        Retrieves a user role data from the database.

        #### Parameters:
        - base_user: An instance of the BaseUser model.

        #### Raises:
        - DatabaseConnectionAPIError: If there is an operational error with the
        database.
        """

        related_model = base_user.content_type.model_class()

        try:
            user_role = related_model.objects.filter(
                uuid=base_user.role_data_uuid
            ).first()
        except OperationalError:
            # In the future, a retry system will be implemented when the database is
            # suddenly unavailable.
            raise DatabaseConnectionAPIError()

        return user_role

    @classmethod
    def role_data_exists(cls, user_role: str, **filters) -> bool:
        """
        Checks if a user role data exists in the database.

        #### Parameters:
        - user_role: Role of the user.
        - filters: Keyword arguments that define the filters to apply.

        #### Raises:
        - DatabaseConnectionAPIError: If there is an operational error with the
        database.
        """

        try:
            content_type = ContentType.objects.get(model=user_role)
            related_model = content_type.model_class()

            exists = related_model.objects.filter(**filters).exists()
        except OperationalError:
            # In the future, a retry system will be implemented when the database is
            # suddenly unavailable.
            raise DatabaseConnectionAPIError()

        return exists

    @classmethod
    def base_data_exists(cls, **filters) -> bool:
        """
        Checks if a user base data exists in the database.

        #### Parameters:
        - filters: Keyword arguments that define the filters to apply.

        #### Raises:
        - DatabaseConnectionAPIError: If there is an operational error with the
        database.
        """

        try:
            exists = cls.model.objects.filter(**filters).exists()
        except OperationalError:
            # In the future, a retry system will be implemented when the database is
            # suddenly unavailable.
            raise DatabaseConnectionAPIError()

        return exists

    @classmethod
    def update_role_data(
        cls,
        base_user: BaseUser,
        data: Dict[str, Any],
    ) -> Model:
        """
        Updates the role data for a user.

        #### Parameters:
        - base_user: An instance of the BaseUser model.
        - data: Dictionary containing the data to update.

        #### Raises:
        - DatabaseConnectionAPIError: If there is an operational error with the
        database.
        """

        role_data = cls.get_role_data(base_user=base_user)

        try:
            for field, value in data.items():
                if field == "cc" and role_data.is_phone_verified:
                    role_data.is_phone_verified = False
                setattr(role_data, field, value)
            role_data.save()
        except OperationalError:
            # In the future, a retry system will be implemented when the database is
            # suddenly unavailable.
            raise DatabaseConnectionAPIError()

        return role_data
