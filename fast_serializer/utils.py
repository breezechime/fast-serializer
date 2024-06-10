# -*- coding:utf-8 -*-
import _thread
import functools


def _recursive_repr(user_function):
    # Decorator to make a repr function return "..." for a recursive
    # call.
    repr_running = set()

    @functools.wraps(user_function)
    def wrapper(self):
        key = id(self), _thread.get_ident()
        if key in repr_running:
            return '...'
        repr_running.add(key)
        try:
            result = user_function(self)
        finally:
            repr_running.discard(key)
        return result
    return wrapper


def _format_type(_type) -> str:
    if hasattr(_type, "__name__"):
        return _type.__name__
    elif hasattr(_type, "__class__"):
        return _type.__class__.__name__
    type_str = str(_type)
    type_str = type_str.replace("<class '", "")
    type_str = type_str if not type_str.endswith("'>") else type_str[:-2]
    return type_str