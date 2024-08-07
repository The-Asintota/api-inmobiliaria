from typing import NewType


Token = NewType("Token", str)
Token.__doc__ = """
    Token that is used in various user-related email communication, the token is
    a unique identifier that ensures the security and validity of the processes
    initiated.
"""
