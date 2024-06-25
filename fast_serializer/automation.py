# -*- coding:utf-8 -*-
from typing import Type, Dict
from .field import Field
from .constants import _DATACLASS_FIELDS_NAME, _T
from .fast_dataclass import generate_fast_dataclass


def getter(cls: Type[_T]) -> Type[_T]:

    def wrap(_cls: Type[_T]):
        return generate_getter(_cls)

    # We're called as @dataclass without parens.
    return wrap(cls)


def generate_getter_func(field_name):
    """Generate getter function for class. 为类生成getter函数"""
    def getter_func_wrapper(self):
        return getattr(self, field_name)
    return getter_func_wrapper


def generate_getter(cls: Type[_T]) -> Type[_T]:
    """Generate getter for class. 为类生成getter"""

    """需要先生成快速数据类"""
    if not hasattr(cls, _DATACLASS_FIELDS_NAME):
        cls: Type[_T] = generate_fast_dataclass(cls)  # type: ignore

    dataclass_fields: Dict[str, Field] = getattr(cls, _DATACLASS_FIELDS_NAME, {})
    for field_name, field in dataclass_fields.items():
        setattr(cls, f'get_{field_name}', generate_getter_func(field_name))
    return cls