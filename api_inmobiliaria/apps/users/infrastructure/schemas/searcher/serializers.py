from apps.users.domain.constants import SearcherProperties, UserProperties
from drf_spectacular.utils import (
    extend_schema_serializer,
    OpenApiExample,
)


SearcherRegisterSerializerSchema = extend_schema_serializer(
    examples=[
        OpenApiExample(
            name="data_valid",
            summary="Register a new user with role searcher.",
            description=f"A valid user registration data. The following validations will be applied:\n- **Name and last_name:** This field is required, must not exceed {SearcherProperties.NAME_MAX_LENGTH.value} characters and must contain only letters and spaces.\n- **Email:** This field is required and must not exceed {UserProperties.EMAIL_MAX_LENGTH.value} characters, must follow standard email format, and must not be in use.\n- **Password:** This field is required and should be between {UserProperties.PASSWORD_MIN_LENGTH.value} and {UserProperties.PASSWORD_MAX_LENGTH.value} characters. It should not be a common password or contain only numbers. \n- **Confirm password:** This field is required and should match the password field.\n\nRequest responses that include messages in Spanish indicate that these are messages intended for use on the frontend by the client.",
            value={
                "name": "Nombres del usuario",
                "last_name": "Apellidos del usuario",
                "email": "user1@email.com",
                "password": "contraseña1234",
                "confirm_password": "contraseña1234",
            },
            request_only=True,
        ),
    ],
)

RoleDataSerializerSchema = extend_schema_serializer(
    examples=[
        OpenApiExample(
            name="data_valid",
            summary="The role data of a user with role searcher.",
            description=f"A valid user data. The following validations will be applied:\n- **Name and last_name:** Must not exceed {SearcherProperties.NAME_MAX_LENGTH.value} characters and must contain only letters and spaces.\n- **Email:** Must not exceed {UserProperties.EMAIL_MAX_LENGTH.value} characters, must follow standard email format and must not be in use.\n- **Identification number (cc):** Must not exceed {SearcherProperties.CC_MAX_LENGTH.value} characters, must be at least {SearcherProperties.CC_MIN_LENGTH.value} characters, must contain only numbers between 0-9 and must not be in use.\n- **Address** Must not exceed {SearcherProperties.ADDRESS_MAX_LENGTH.value} characters and must not be in use.\n- **Phone number** Must not exceed {SearcherProperties.PHONE_NUMBER_MAX_LENGTH.value} characters and must not be in use.",
            value={
                "base_data": {"email": "user1@email.com"},
                "role_data": {
                    "name": "Nuevo nombre",
                    "last_name": "Nuevo apellido",
                    "cc": "1234567890",
                    "address": "Nueva dirección",
                    "phone_number": "+57 3111111111",
                },
            },
            request_only=True,
        ),
    ],
)
