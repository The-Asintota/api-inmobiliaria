from apps.users.domain.constants import UserProperties
from apps.utils import ERROR_MESSAGES
from rest_framework.fields import CharField
from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiExample,
)


# This constant is used when the serializer error messages are the default.
DEFAULT_ERROR_MESSAGES = CharField().error_messages


AuthenticationSchema = extend_schema(
    operation_id="jwt_authenticate_user",
    tags=["Users"],
    responses={
        200: OpenApiResponse(
            description="**(OK)** Authenticated user.",
            response={
                "properties": {
                    "access": {"type": "string"},
                    "refresh": {"type": "string"},
                }
            },
            examples=[
                OpenApiExample(
                    name="response_ok",
                    summary="User authenticated",
                    description="The user has been authenticated successfully and the access and refresh tokens are returned. The access token is used to authenticate the user in the application, while the refresh token is used to obtain a new access token, each of these tokens contains information about the user, such as the user's identifier, the type of token, the expiration date, and the date of issue.",
                    value={
                        "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzExMDU0MzYyLCJpYXQiOjE3MTEwNDcxNjIsImp0aSI6IjY0MTE2YzgyYjhmMDQzOWJhNTJkZGZmMzgyNzQ2ZTIwIiwidXNlcl9pZCI6IjJhNmI0NTNiLWZhMmItNDMxOC05YzM1LWIwZTk2ZTg5NGI2MyJ9.gfhWpy5rYY6P3Xrg0usS6j1KhEvF1HqWMiU7AaFkp9A",
                        "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTcxMTEzMzU2MiwiaWF0IjoxNzExMDQ3MTYyLCJqdGkiOiI2ZTRmNTdkMGJjNTc0NWY0OWMzODg4YjQ2YTM1OTJjNSIsInVzZXJfaWQiOiIyYTZiNDUzYi1mYTJiLTQzMTgtOWMzNS1iMGU5NmU4OTRiNjMifQ.81pQ3WftFZs5O50vGqwY2a6yPkXArQK6WKyrwus3s6A",
                    },
                ),
            ],
        ),
        400: OpenApiResponse(
            description="**(BAD_REQUEST)** The request data are invalid, error message(s) are returned for each field that did not pass the validations.",
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
                            "email": [
                                ERROR_MESSAGES["required"],
                                ERROR_MESSAGES["blank"],
                                ERROR_MESSAGES["null"],
                                ERROR_MESSAGES["max_length"].format(
                                    max_length=UserProperties.EMAIL_MAX_LENGTH.value,
                                ),
                            ],
                            "password": [
                                ERROR_MESSAGES["required"],
                                ERROR_MESSAGES["blank"],
                                ERROR_MESSAGES["null"],
                                ERROR_MESSAGES["max_length"].format(
                                    max_length=UserProperties.PASSWORD_MAX_LENGTH.value,
                                ),
                            ],
                        },
                    },
                ),
            ],
        ),
        401: OpenApiResponse(
            description="**(UNAUTHORIZED)** The user you are trying to authenticate is not authorized, this is due to some of the following reasons.\n- Invalid credentials.\n- The user's account has not been activated.",
            response={
                "properties": {
                    "code": {"type": "string"},
                    "detail": {"type": "string"},
                }
            },
            examples=[
                OpenApiExample(
                    name="authentication_failed",
                    summary="Credentials invalid",
                    description="The email or password provided is incorrect.",
                    value={
                        "code": "authentication_failed",
                        "detail": "Credenciales inválidas.",
                    },
                ),
                OpenApiExample(
                    name="user_inactive",
                    summary="Inactive user account",
                    description="The user account is inactive.",
                    value={
                        "code": "authentication_failed",
                        "detail": "Cuenta del usuario inactiva.",
                    },
                ),
            ],
        ),
        403: OpenApiResponse(
            description="**(FORBIDDEN)** The user trying to authenticate does not have the permissions to do so with JSON Web Token.",
            response={
                "properties": {
                    "code": {"type": "string"},
                    "detail": {"type": "string"},
                }
            },
            examples=[
                OpenApiExample(
                    name="permission_denied",
                    summary="Permission denied",
                    description="This response appears when the user trying to authenticate does not have the permissions to do so with JSON Web Token.",
                    value={
                        "code": "permission_denied",
                        "detail": "The user does not have permissions to perform this action.",
                    },
                ),
            ],
        ),
        500: OpenApiResponse(
            description="**(INTERNAL_SERVER_ERROR)** An unexpected error occurred.",
            response={
                "properties": {
                    "detail": {"type": "string"},
                    "code": {"type": "string"},
                }
            },
            examples=[
                OpenApiExample(
                    name="database_connection_error",
                    summary="Database connection error",
                    description="The connection to the database could not be established.",
                    value={
                        "code": "database_connection_error",
                        "detail": "Unable to establish a connection with the database. Please try again later.",
                    },
                ),
            ],
        ),
    },
)


UpdateTokensSchema = extend_schema(
    operation_id="update_tokens",
    tags=["Users"],
    responses={
        200: OpenApiResponse(
            description="**(OK)** New tokens are generated.",
            response={
                "properties": {
                    "access": {"type": "string"},
                    "refresh": {"type": "string"},
                }
            },
            examples=[
                OpenApiExample(
                    name="response_ok",
                    summary="New tokens generated",
                    description="The new access and refresh tokens have been generated successfully, you can use these new tokens to keep the user authenticated.",
                    value={
                        "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzE1NjQ4MTAyLCJpYXQiOjE3MTU2NDA5MDIsImp0aSI6ImQ0YzEwYzEzMTgwODQ3YmNiNGU5NDMwMjFhYmQ3OGMyIiwidXNlcl91dWlkIjoiZDdiYTM0NzEtZWQzOS00NTQxLWFmOTktZWVmYzFjMWRlYmJkIiwicm9sZSI6IlNlYXJjaGVyVXNlciJ9.C5W1Q4XLBRXUbSUtKcESvudwo6-Ylg8u1fZZ4i79GWw",
                        "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTcxNTcyNzMwMiwiaWF0IjoxNzE1NjQwOTAyLCJqdGkiOiI0YjgwNjA2YTk3ODI0Y2U3YjZjNzIxZTBkYTE3YmUzMiIsInVzZXJfdXVpZCI6ImQ3YmEzNDcxLWVkMzktNDU0MS1hZjk5LWVlZmMxYzFkZWJiZCIsInJvbGUiOiJTZWFyY2hlclVzZXIifQ.JpRoGrk7GVDQmHrJnc1LelgzGMKmKvmXYKvAKQzhsWg",
                    },
                ),
            ],
        ),
        400: OpenApiResponse(
            description="**(BAD_REQUEST)** The request data are invalid, error message(s) are returned for each field that did not pass the validations.",
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
                            "refresh": [
                                DEFAULT_ERROR_MESSAGES["required"],
                                DEFAULT_ERROR_MESSAGES["blank"],
                                DEFAULT_ERROR_MESSAGES["null"],
                                DEFAULT_ERROR_MESSAGES["invalid"],
                                "Token is expired.",
                                "Token is invalid.",
                            ],
                            "access": [
                                DEFAULT_ERROR_MESSAGES["required"],
                                DEFAULT_ERROR_MESSAGES["blank"],
                                DEFAULT_ERROR_MESSAGES["null"],
                                DEFAULT_ERROR_MESSAGES["invalid"],
                                "Token is invalid.",
                                "Token is not expired.",
                            ],
                        },
                    },
                ),
            ],
        ),
        401: OpenApiResponse(
            description="**(UNAUTHORIZED)** The user's JSON Web Token is not valid for logout.",
            response={
                "properties": {
                    "code": {"type": "string"},
                    "detail": {"type": "string"},
                }
            },
            examples=[
                OpenApiExample(
                    name="token_error",
                    summary="Token error",
                    description="The provided JSON Web Tokens do not match the user's last generated tokens.",
                    value={
                        "code": "token_error",
                        "detail": "The JSON Web Tokens does not match the user's last tokens.",
                    },
                ),
            ],
        ),
        404: OpenApiResponse(
            description="**(NOT_FOUND)** Some resources necessary for this process were not found in the database.",
            response={
                "properties": {
                    "code": {"type": "string"},
                    "detail": {"type": "string"},
                }
            },
            examples=[
                OpenApiExample(
                    name="token_not_found",
                    summary="Token not found",
                    description="The JSON Web Tokens provided do not exist in the database.",
                    value={
                        "code": "token_not_found",
                        "detail": "JSON Web Tokens not found.",
                    },
                ),
                OpenApiExample(
                    name="user_not_found",
                    summary="User not found",
                    description="The user in the provided JSON Web Tokens does not exist in the database.",
                    value={
                        "code": "user_not_found",
                        "detail": "The JSON Web Token user does not exist.",
                    },
                ),
            ],
        ),
        500: OpenApiResponse(
            description="**(INTERNAL_SERVER_ERROR)** An unexpected error occurred.",
            response={
                "properties": {
                    "detail": {"type": "string"},
                    "code": {"type": "string"},
                }
            },
            examples=[
                OpenApiExample(
                    name="database_connection_error",
                    summary="Database connection error",
                    description="The connection to the database could not be established.",
                    value={
                        "code": "database_connection_error",
                        "detail": "Unable to establish a connection with the database. Please try again later.",
                    },
                ),
            ],
        ),
    },
)


LogoutSchema = extend_schema(
    operation_id="logout_user",
    tags=["Users"],
    responses={
        200: OpenApiResponse(
            description="**(OK)** Successfully closed session.",
        ),
        401: OpenApiResponse(
            description="**(UNAUTHORIZED)** The user's JSON Web Token is not valid for logout.",
            response={
                "properties": {
                    "code": {"type": "string"},
                    "detail": {"type": "string"},
                }
            },
            examples=[
                OpenApiExample(
                    name="token_error",
                    summary="Token error",
                    description="The provided JSON Web Tokens do not match the user's last generated tokens.",
                    value={
                        "code": "token_error",
                        "detail": "The JSON Web Tokens does not match the user's last tokens.",
                    },
                ),
            ],
        ),
        404: OpenApiResponse(
            description="**(NOT_FOUND)** Some resources necessary for this process were not found in the database.",
            response={
                "properties": {
                    "code": {"type": "string"},
                    "detail": {"type": "string"},
                }
            },
            examples=[
                OpenApiExample(
                    name="token_not_found",
                    summary="Token not found",
                    description="The JSON Web Tokens provided do not exist in the database.",
                    value={
                        "code": "token_not_found",
                        "detail": "JSON Web Tokens not found.",
                    },
                ),
                OpenApiExample(
                    name="user_not_found",
                    summary="User not found",
                    description="The user in the provided JSON Web Tokens does not exist in the database.",
                    value={
                        "code": "user_not_found",
                        "detail": "The JSON Web Token user does not exist.",
                    },
                ),
            ],
        ),
        500: OpenApiResponse(
            description="**(INTERNAL_SERVER_ERROR)** An unexpected error occurred.",
            response={
                "properties": {
                    "detail": {"type": "string"},
                    "code": {"type": "string"},
                }
            },
            examples=[
                OpenApiExample(
                    name="database_connection_error",
                    summary="Database connection error",
                    description="The connection to the database could not be established.",
                    value={
                        "code": "database_connection_error",
                        "detail": "Unable to establish a connection with the database. Please try again later.",
                    },
                ),
            ],
        ),
    },
)
