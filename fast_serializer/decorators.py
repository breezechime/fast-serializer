# -*- coding:utf-8 -*-
from typing import Union, Any, Callable, Optional, Dict, Type
from .field import Field
from dataclasses import dataclass, field as dataclass_field


@dataclass
class Decorator:
    """基础的装饰器信息"""

    clazz: str
    class_name: str
    func: Callable[..., Any]


@dataclass
class FieldValidatorDecoratorInfo(Decorator):
    """自定义字段验证装饰器"""

    fields: tuple[str, ...]


@dataclass
class FastDataclassDecoratorInfo:
    """快速数据类装饰器信息"""

    field_validators: Dict[str, FieldValidatorDecoratorInfo] = dataclass_field(default_factory=dict)

    @classmethod
    def build(cls, fast_dataclass: Type[Any]):
        decorator_info = cls()

        return decorator_info


def field_serializer(*fields: Union[str, Field]):
    """自定义字段序列化"""
    pass


def field_validator(field: Union[str, Field], *fields: Union[str, Field]):
    """自定义字段验证"""
    fields = field, *fields
    fields = [field.name if isinstance(field, Field) else field for field in fields]
    if not all(isinstance(field, str) for field in fields):
        raise RuntimeError(
            '`@field_validator` 字段应作为单独的字符串或字段参数传递。 '
            "E.g. usage should be `@validator('<field_name_1>', '<field_name_2>', ...)`"
        )


def type_serializer(_type: Any):
    """自定义类型序列化"""
    pass


def type_validator(_type: Any):
    """自定义类型验证"""
    pass


def dataclass_serializer(func: Optional[Callable[..., Any]] = None):
    """自定义数据类序列化"""
    pass


def dataclass_validator(func: Optional[Callable[..., Any]] = None):
    """自定义数据类序列化"""
    pass