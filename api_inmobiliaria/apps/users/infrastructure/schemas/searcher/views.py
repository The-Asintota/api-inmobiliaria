from apps.users.domain.constants import SearcherProperties, UserProperties
from apps.api_exceptions import DatabaseConnectionAPIError
from apps.utils import ERROR_MESSAGES
from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiExample,
)


SearcherRegisterSchema = extend_schema(
    operation_id="create_searcher_user",
    tags=["Users"],
    responses={
        201: OpenApiResponse(
            description="**(CREATED)** User created correctly."
        ),
        400: OpenApiResponse(
            description="**(BAD_REQUEST)** The request data is invalid, error messages are returned for each field that did not pass validations.",
            response={
                "properties": {
                    "code": {"type": "string"},
                    "detail": {"type": "object"},
                }
            },
            examples=[
                OpenApiExample(
                    name="invalid_data",
                    summary="Invalid data",
                    description="These are the possible error messages for each field.",
                    value={
                        "code": "invalid_request_data",
                        "detail": {
                            "name": [
                                ERROR_MESSAGES["required"],
                                ERROR_MESSAGES["blank"],
                                ERROR_MESSAGES["null"],
                                ERROR_MESSAGES["invalid"],
                                ERROR_MESSAGES["max_length"].format(
                                    max_length=SearcherProperties.NAME_MAX_LENGTH.value,
                                ),
                            ],
                            "last_name": [
                                ERROR_MESSAGES["required"],
                                ERROR_MESSAGES["blank"],
                                ERROR_MESSAGES["null"],
                                ERROR_MESSAGES["invalid"],
                                ERROR_MESSAGES["max_length"].format(
                                    max_length=SearcherProperties.LAST_NAME_MAX_LENGTH.value,
                                ),
                            ],
                            "email": [
                                ERROR_MESSAGES["required"],
                                ERROR_MESSAGES["blank"],
                                ERROR_MESSAGES["null"],
                                ERROR_MESSAGES["invalid"],
                                ERROR_MESSAGES["max_length"].format(
                                    max_length=UserProperties.EMAIL_MAX_LENGTH.value,
                                ),
                                ERROR_MESSAGES["email_in_use"],
                            ],
                            "password": [
                                ERROR_MESSAGES["required"],
                                ERROR_MESSAGES["blank"],
                                ERROR_MESSAGES["null"],
                                ERROR_MESSAGES["invalid"],
                                ERROR_MESSAGES["max_length"].format(
                                    max_length=UserProperties.PASSWORD_MAX_LENGTH.value,
                                ),
                                ERROR_MESSAGES["min_length"].format(
                                    min_length=UserProperties.PASSWORD_MIN_LENGTH.value,
                                ),
                            ],
                            "confirm_password": [
                                ERROR_MESSAGES["required"],
                                ERROR_MESSAGES["blank"],
                                ERROR_MESSAGES["null"],
                                ERROR_MESSAGES["password_no_upper_lower"],
                                ERROR_MESSAGES["password_common"],
                                ERROR_MESSAGES["password_mismatch"],
                            ],
                        },
                    },
                ),
            ],
        ),
        500: OpenApiResponse(
            description="**(INTERNAL_SERVER_ERROR)** An unexpected error occurred.",
            response={
                "properties": {
                    "detail": {
                        "type": "string",
                    },
                    "code": {
                        "type": "string",
                    },
                }
            },
            examples=[
                OpenApiExample(
                    name="database_connection_error",
                    summary="Database connection error",
                    description="The connection to the database could not be established.",
                    value={
                        "code": DatabaseConnectionAPIError.default_code,
                        "detail": DatabaseConnectionAPIError.default_detail,
                    },
                ),
            ],
        ),
    },
)
