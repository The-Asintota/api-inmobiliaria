from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.auth.models import (
    UserManager as BaseUserManager,
    AbstractBaseUser,
    PermissionsMixin,
)
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from apps.users.domain.constants import UserProperties, SearcherProperties
from typing import Dict, Any
from uuid import uuid4


class UserManager(BaseUserManager):
    """
    Manager for the user model, provides methods to create user and superuser
    instances.
    """

    def _create_user(
        self,
        related_model_name: str = None,
        role_data: Dict[str, Any] = None,
        base_data: Dict[str, Any] = None,
    ) -> AbstractBaseUser:
        """
        This is a private method that handles the creation of a user instance.
        Optionally it can associate to a model instance that encapsulates the user
        role data if `related_model_name` and `role_data` are provided.
        """

        related_instance = None

        if related_model_name and role_data:
            related_model = ContentType.objects.get(
                model=related_model_name
            ).model_class()
            related_instance = related_model.objects.create(**role_data)

        email = base_data.pop("email")
        password = base_data.pop("password")
        user: AbstractBaseUser = self.model(
            email=self.normalize_email(email),
            content_object=related_instance,
            **base_data,
        )
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_user(
        self,
        is_active: bool = None,
        related_model_name: str = None,
        role_data: Dict[str, Any] = None,
        base_data: Dict[str, Any] = None,
    ) -> AbstractBaseUser:
        """
        Creates and saves a user with the specified attributes.

        #### Parameters:
        - is_active: Indicates if the user is active.
        - related_model_name: The name of the related model that encapsulates the
        role data.
        - role_data: The data to create the related model instance.
        - base_data: The data to create the user instance.
        """

        base_data.setdefault("is_active", is_active or False)

        return self._create_user(
            related_model_name=related_model_name,
            role_data=role_data,
            base_data=base_data,
        )

    def create_superuser(
        self,
        email: str,
        password: str,
        **base_data,
    ) -> AbstractBaseUser:
        """
        Create and save a SuperUser with the given email and password.
        """

        base_data.setdefault("is_staff", True)
        base_data.setdefault("is_superuser", True)
        base_data.setdefault("is_active", True)

        if base_data.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        elif base_data.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        elif base_data.get("is_active") is not True:
            raise ValueError("Superuser must have is_active=True.")

        base_data["email"] = email
        base_data["password"] = password

        return self._create_user(base_data=base_data)


class BaseUser(AbstractBaseUser, PermissionsMixin):
    """
    This object encapsulates the `base data` of a user, which is essential for
    authentication, permission validation and security processes.

    It also includes a `generic relationship` that allows the association of a user
    role data. This relationship facilitates the linking with different objects that
    encapsulate the data of the different roles that a user can have in the system.
    """

    uuid = models.UUIDField(
        db_column="uuid",
        default=uuid4,
        primary_key=True,
        null=False,
        blank=False,
    )
    email = models.EmailField(
        db_column="email",
        max_length=UserProperties.EMAIL_MAX_LENGTH.value,
        unique=True,
        null=False,
        blank=False,
    )
    password = models.CharField(
        db_column="password", max_length=128, null=False, blank=False
    )
    content_type = models.ForeignKey(
        db_column="content_type",
        to=ContentType,
        on_delete=models.SET_NULL,
        null=True,
    )
    role_data_uuid = models.UUIDField(
        db_column="role_data_uuid",
        null=True,
        blank=True,
    )
    content_object = GenericForeignKey(
        ct_field="content_type", fk_field="role_data_uuid"
    )
    is_staff = models.BooleanField(db_column="is_staff", default=False)
    is_superuser = models.BooleanField(db_column="is_superuser", default=False)
    is_active = models.BooleanField(db_column="is_active", default=False)
    is_deleted = models.BooleanField(db_column="is_deleted", default=False)
    deleted_at = models.DateTimeField(db_column="deleted_at", null=True)
    last_login = models.DateTimeField(db_column="last_login", null=True)
    date_joined = models.DateTimeField(
        db_column="date_joined", auto_now_add=True
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self) -> str:
        """
        Return the string representation of the model.
        """

        return self.email


class Searcher(models.Model):
    """
    This object encapsulates the `role data` of a searcher user.
    """

    uuid = models.UUIDField(db_column="uuid", default=uuid4, primary_key=True)
    name = models.CharField(
        db_column="name",
        max_length=SearcherProperties.NAME_MAX_LENGTH.value,
        null=False,
        blank=False,
    )
    last_name = models.CharField(
        db_column="last_name",
        max_length=SearcherProperties.LAST_NAME_MAX_LENGTH.value,
        null=False,
        blank=False,
    )
    cc = models.CharField(
        db_column="cc",
        max_length=SearcherProperties.CC_MAX_LENGTH.value,
        null=True,
        blank=True,
        unique=True,
    )
    address = models.CharField(
        db_column="address",
        max_length=SearcherProperties.ADDRESS_MAX_LENGTH.value,
        null=True,
        blank=True,
        unique=True,
    )
    phone_number = PhoneNumberField(
        db_column="phone_number",
        max_length=SearcherProperties.PHONE_NUMBER_MAX_LENGTH.value,
        null=True,
        blank=True,
        unique=True,
    )
    is_phone_verified = models.BooleanField(
        db_column="is_phone_verified", default=False
    )

    class Meta:
        verbose_name = "searcher"
        verbose_name_plural = "searchers"

    def __str__(self) -> str:
        """
        Return the string representation of the model.
        """

        return self.uuid.__str__()

    def get_full_name(self) -> str:
        """
        Return the full name of the user.
        """

        return f"{self.name.capitalize()} {self.last_name.capitalize()}"
