from uuid import UUID
import base64


def is_valid_uuid(value: str) -> bool:
    """
    Validates if the provided string is a valid UUID.
    """

    try:
        UUID(value)

        return True
    except ValueError:
        return False


def is_base64(value: str) -> bool:
    """
    Check if the provided string is a valid base64 string.
    """

    try:
        return base64.b64encode(s=base64.b64decode(s=value)).decode() == value
    except Exception:

        return False
