# -*- coding:utf-8 -*-
import decimal
from typing import Type, Optional, Dict, Any, ClassVar, get_type_hints
from .field import Field
from .constants import _T, _DATACLASS_FIELDS_NAME
from .utils import _format_type
from .validator import DEFAULT_VALIDATORS, Validator


class FastSerializer:
    """序列化器提供强大的序列化和反序列化"""

    """内置默认的验证器"""
    __default_validators__: ClassVar[Dict[str, Validator]] = DEFAULT_VALIDATORS

    def __init__(self):
        self.field_validators: Dict[str, Validator] = {}  # 自定义的字段验证器
        self.type_validators: Dict[str, Validator] = {}  # 用户编写的自定义类型验证器

    def deserialize(self, data: dict, target: Optional[Type[_T]] = None, instance: Optional[_T] = None) -> _T:
        """反序列化 Deserialize"""
        if target is None and instance is None:
            raise RuntimeError('target and instance cannot be None at the same time')

        if instance is None:
            instance: _T = target()  # type: ignore

        dataclass_fields: Dict[str, Field] = getattr(instance.__class__, _DATACLASS_FIELDS_NAME, {})
        for field_name, field in dataclass_fields.items():
            value = self._get_value(data, field_name, field)

            """数据为必填项"""
            if value is None and field.required:
                raise ValueError(f"{field_name} 为必填项")

            """反序列化过程中类型如果不正确会进行强行转换"""
            if value is not None and not isinstance(value, field.type):
                value = self._convert_value_type(value, field.type)

            setattr(instance, field_name, value)

        return instance  # type: ignore

    @staticmethod
    def _get_value(data: dict, field_name: str, field: Field) -> Any:
        try:
            value = data[field_name]
        except KeyError:
            value = field.default if field.default is not None else None
            value = field.default_factory() if value is None and field.default_factory is not None else None
        return value

    def _convert_value_type(self, value, _type):
        """内置验证器会尝试帮你转换类型，如果不成功将抛出异常"""
        if _type in self.type_validators:
            return self.type_validators[_type].validate(value)
        if _type in self.__default_validators__:
            return self.__default_validators__[_type].validate(value)
        else:
            print(f"类型 {_format_type(_type)} 未被支持")
            return value