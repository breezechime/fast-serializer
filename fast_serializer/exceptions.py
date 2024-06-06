# -*- coding:utf-8 -*-
from typing import (
    TypedDict,
    Any
)
from .types import optional


class ErrorDetails(TypedDict):
    type: str
    """
    The type of error that occurred, this is an identifier designed for
    programmatic use that will change rarely or never.

    `type` is unique for each error message, and can hence be used as an identifier to build custom error messages.
    """
    loc: tuple[int | str, ...]
    """Tuple of strings and ints identifying where in the schema the error occurred."""
    msg: str
    """A human readable error message."""
    input: Any
    """The input data at this `loc` that caused the error."""
    ctx: optional[dict[str, Any]]
    """
    Values which are required to render the error message, and could hence be useful in rendering custom error messages.
    Also useful for passing custom error data forward.
    """


class ValidationError(ValueError):

    def __init__(self, *args):
        super().__init__(*args)

    def errors(self):
        pass

    def error_count(self):
        pass

    def json(self):
        pass

    def __str__(self):
        pass

    def __repr__(self):
        pass


class DataclassCustomError(ValueError):
    pass