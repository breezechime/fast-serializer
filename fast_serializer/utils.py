# -*- coding:utf-8 -*-
import _thread
import functools
from typing import Union

from .constants import _SUB_VALIDATOR_KWARGS_NAME


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


def camel_to_snake(text: str) -> str:
    """驼峰转下划线"""
    return ''.join(['_' + i.lower() if i.isupper() else i for i in text]).lstrip('_')


def snake_to_camel(text: str) -> str:
    """下划线转驼峰"""
    return ''.join(w.capitalize() for w in text.split('_'))


def isinstance_safe(v, tp) -> bool:
    """安全的检查类型"""
    try:
        return isinstance(v, tp)
    except (Exception,):
        return False


def issubclass_safe(v, tp) -> bool:
    try:
        return issubclass(v, tp)
    except (Exception,):
        return False


def get_sub_validator_kwargs(validator_kwargs: Union[dict, list], index: int = 0) -> dict:
    try:
        sub_validator_kwargs = validator_kwargs[_SUB_VALIDATOR_KWARGS_NAME]
        if isinstance(sub_validator_kwargs, dict):
            del validator_kwargs[_SUB_VALIDATOR_KWARGS_NAME]
            return sub_validator_kwargs
        else:
            kwargs = sub_validator_kwargs[index]
            if index == len(sub_validator_kwargs) - 1:
                validator_kwargs.pop(_SUB_VALIDATOR_KWARGS_NAME)
            return kwargs
    except (KeyError,):
        return dict()
