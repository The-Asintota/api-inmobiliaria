from apps.users.domain.constants import (
    ACCESS_TOKEN_LIFETIME,
    REFRESH_TOKEN_LIFETIME,
    UserProperties,
    UserRoles,
)
from apps.utils.messages import ERROR_MESSAGES, JWTErrorMessages
from apps.permissions import IsJWTOwner
from apps.api_exceptions import (
    PermissionDeniedAPIError,
    DatabaseConnectionAPIError,
    AuthenticationFailedAPIError,
    NotAuthenticatedAPIError,
    JWTAPIError,
)
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
    auth=[],
    responses={
        200: OpenApiResponse(
            description="**(OK)** Authenticated user.",
            response={
                "properties": {
                    "access_token": {"type": "string"},
                    "refresh_token": {"type": "string"},
                    "role_user": {"type": "string"},
                }
            },
            examples=[
                OpenApiExample(
                    name="response_ok",
                    summary="User authenticated",
                    description=f"The user has been successfully authenticated and the access and refresh tokens are returned. The access token with a duration of {ACCESS_TOKEN_LIFETIME} minutes used to access protected API resources. This token is sent with each request to the server to authenticate the user, while the refresh token with a duration of {REFRESH_TOKEN_LIFETIME} day that is used to obtain new JSON Web Tokens without requiring the user to authenticate again. This is useful when the access token has expired, but the user should still be authenticated.",
                    value={
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzExMDU0MzYyLCJpYXQiOjE3MTEwNDcxNjIsImp0aSI6IjY0MTE2YzgyYjhmMDQzOWJhNTJkZGZmMzgyNzQ2ZTIwIiwidXNlcl9pZCI6IjJhNmI0NTNiLWZhMmItNDMxOC05YzM1LWIwZTk2ZTg5NGI2MyJ9.gfhWpy5rYY6P3Xrg0usS6j1KhEvF1HqWMiU7AaFkp9A",
                        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTcxMTEzMzU2MiwiaWF0IjoxNzExMDQ3MTYyLCJqdGkiOiI2ZTRmNTdkMGJjNTc0NWY0OWMzODg4YjQ2YTM1OTJjNSIsInVzZXJfaWQiOiIyYTZiNDUzYi1mYTJiLTQzMTgtOWMzNS1iMGU5NmU4OTRiNjMifQ.81pQ3WftFZs5O50vGqwY2a6yPkXArQK6WKyrwus3s6A",
                        "role_user": UserRoles.SEARCHER.value,
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
                                ERROR_MESSAGES["invalid"],
                                ERROR_MESSAGES["max_length"].format(
                                    max_length=UserProperties.EMAIL_MAX_LENGTH.value,
                                ),
                            ],
                            "password": [
                                ERROR_MESSAGES["required"],
                                ERROR_MESSAGES["blank"],
                                ERROR_MESSAGES["null"],
                                ERROR_MESSAGES["invalid"],
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
                        "code": AuthenticationFailedAPIError.default_code,
                        "detail": JWTErrorMessages.AUTHENTICATION_FAILED.value,
                    },
                ),
                OpenApiExample(
                    name="user_inactive",
                    summary="Inactive user account",
                    description="The user account is inactive.",
                    value={
                        "code": AuthenticationFailedAPIError.default_code,
                        "detail": JWTErrorMessages.INACTIVE_ACCOUNT.value,
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
                        "code": PermissionDeniedAPIError.default_code,
                        "detail": PermissionDeniedAPIError.default_detail,
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
                        "code": DatabaseConnectionAPIError.default_code,
                        "detail": DatabaseConnectionAPIError.default_detail,
                    },
                ),
            ],
        ),
    },
)


UpdateTokensSchema = extend_schema(
    operation_id="update_tokens",
    tags=["Users"],
    auth=[],
    responses={
        200: OpenApiResponse(
            description="**(OK)** New tokens are generated.",
            response={
                "properties": {
                    "access_token": {"type": "string"},
                    "refresh_token": {"type": "string"},
                }
            },
            examples=[
                OpenApiExample(
                    name="response_ok",
                    summary="New tokens generated",
                    description="The new access and refresh tokens have been generated successfully, you can use these new tokens to keep the user authenticated.",
                    value={
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzE1NjQ4MTAyLCJpYXQiOjE3MTU2NDA5MDIsImp0aSI6ImQ0YzEwYzEzMTgwODQ3YmNiNGU5NDMwMjFhYmQ3OGMyIiwidXNlcl91dWlkIjoiZDdiYTM0NzEtZWQzOS00NTQxLWFmOTktZWVmYzFjMWRlYmJkIiwicm9sZSI6IlNlYXJjaGVyVXNlciJ9.C5W1Q4XLBRXUbSUtKcESvudwo6-Ylg8u1fZZ4i79GWw",
                        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTcxNTcyNzMwMiwiaWF0IjoxNzE1NjQwOTAyLCJqdGkiOiI0YjgwNjA2YTk3ODI0Y2U3YjZjNzIxZTBkYTE3YmUzMiIsInVzZXJfdXVpZCI6ImQ3YmEzNDcxLWVkMzktNDU0MS1hZjk5LWVlZmMxYzFkZWJiZCIsInJvbGUiOiJTZWFyY2hlclVzZXIifQ.JpRoGrk7GVDQmHrJnc1LelgzGMKmKvmXYKvAKQzhsWg",
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
                            "refresh_token": [
                                DEFAULT_ERROR_MESSAGES["required"],
                                DEFAULT_ERROR_MESSAGES["blank"],
                                DEFAULT_ERROR_MESSAGES["null"],
                                DEFAULT_ERROR_MESSAGES["invalid"],
                            ],
                            "access_token": [
                                DEFAULT_ERROR_MESSAGES["required"],
                                DEFAULT_ERROR_MESSAGES["blank"],
                                DEFAULT_ERROR_MESSAGES["null"],
                                DEFAULT_ERROR_MESSAGES["invalid"],
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
                    name="invalid_expired",
                    summary="Invalid or expired",
                    description="The access or refresh token is invalid or has expired.",
                    value={
                        "code": JWTAPIError.default_code,
                        "detail": JWTErrorMessages.INVALID_OR_EXPIRED.value.format(
                            token_type="refresh",
                        ),
                    },
                ),
                OpenApiExample(
                    name="token_blacklisted",
                    summary="Token exists in the blacklist",
                    description="The access token exists in the blacklist. Tokens that exist in the blacklist cannot be used in authentication processes and creation of new tokens.",
                    value={
                        "code": JWTAPIError.default_code,
                        "detail": JWTErrorMessages.BLACKLISTED.value.format(
                            token_type="access",
                        ),
                    },
                ),
                OpenApiExample(
                    name="access_token_not_expired",
                    summary="Access token not expired",
                    description="New JSON Web Tokens can only be created for a user if their access token has expired.",
                    value={
                        "code": JWTAPIError.default_code,
                        "detail": JWTErrorMessages.ACCESS_NOT_EXPIRED.value,
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
                        "code": JWTErrorMessages.TOKEN_NOT_FOUND.value["code"],
                        "detail": JWTErrorMessages.TOKEN_NOT_FOUND.value[
                            "detail"
                        ].format(token_type="access or refresh"),
                    },
                ),
                OpenApiExample(
                    name="user_not_found",
                    summary="User not found",
                    description="The user in the provided JSON Web Tokens does not exist in the database.",
                    value=JWTErrorMessages.USER_NOT_FOUND.value,
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
                        "code": DatabaseConnectionAPIError.default_code,
                        "detail": DatabaseConnectionAPIError.default_detail,
                    },
                ),
            ],
        ),
    },
)


LogoutSchema = extend_schema(
    operation_id="logout_user",
    tags=["Users"],
    auth=[{"JWTAuthentication": []}],
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
                    name="invalid_expired",
                    summary="Invalid or expired",
                    description="The access or refresh token is invalid or has expired.",
                    value={
                        "code": JWTAPIError.default_code,
                        "detail": JWTErrorMessages.INVALID_OR_EXPIRED.value.format(
                            token_type="access",
                        ),
                    },
                ),
                OpenApiExample(
                    name="token_blacklisted",
                    summary="Token exists in the blacklist",
                    description="The access token exists in the blacklist. Tokens that exist in the blacklist cannot be used in authentication processes and creation of new tokens.",
                    value={
                        "code": JWTAPIError.default_code,
                        "detail": JWTErrorMessages.BLACKLISTED.value.format(
                            token_type="access",
                        ),
                    },
                ),
                OpenApiExample(
                    name="access_token_not_provided",
                    summary="Access token not provided",
                    description="The access token was not provided.",
                    value={
                        "code": NotAuthenticatedAPIError.default_code,
                        "detail": NotAuthenticatedAPIError.default_detail,
                    },
                ),
            ],
        ),
        403: OpenApiResponse(
            description="**(FORBIDDEN)** The user does not have permission to access this resource.",
            response={
                "properties": {
                    "code": {"type": "string"},
                    "detail": {"type": "string"},
                }
            },
            examples=[
                OpenApiExample(
                    name="is_jwt_owner",
                    summary="User is not the owner of the JWT",
                    description="The user making the request is not the owner of the JWT.",
                    value={
                        "code": IsJWTOwner.code,
                        "detail": IsJWTOwner.message,
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
                    name="user_not_found",
                    summary="User not found",
                    description="The user in the provided JSON Web Tokens does not exist in the database.",
                    value=JWTErrorMessages.USER_NOT_FOUND.value,
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
                        "code": DatabaseConnectionAPIError.default_code,
                        "detail": DatabaseConnectionAPIError.default_detail,
                    },
                ),
            ],
        ),
    },
)
