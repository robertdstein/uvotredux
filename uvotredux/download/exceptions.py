"""
Custom exceptions for the download module.
"""


class SwiftAPIError(Exception):
    """
    Raised when a request to the Swift TOO API does not succeed,
    e.g. due to a timeout, rejection, or network error.
    """
