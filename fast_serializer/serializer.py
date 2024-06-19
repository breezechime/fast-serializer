# -*- coding:utf-8 -*-
import enum
from typing import Type, Optional, Dict, Any, ClassVar, Union, Callable
from .field import Field
from .constants import _T, _DATACLASS_FIELDS_NAME
from .type_parser import type_parser
from .utils import _format_type
from .validator import BASE_VALIDATORS, Validator, EnumValidator, TupleValidator


class FastSerializer:
    """序列化器提供强大的序列化和反序列化"""

    """内置基本数据类型验证器"""
    __base_validators__: ClassVar[Dict[str, Validator]] = BASE_VALIDATORS

    def __init__(self):
        self.field_validators: Dict[str, Validator] = {}  # 自定义的字段验证器
        # self.type_validators: Dict[Any, Validator] = {}  # 用户编写的自定义类型验证器

    def deserialize(self, data: Union[dict, object], target: Optional[Type[_T]] = None, instance: Optional[_T] = None) -> _T:
        """反序列化 Deserialize"""
        if target is None and instance is None:
            raise RuntimeError('目标类和实例不能为空')

        if target is None:
            target: Type[_T] = instance.__class__  # type: ignore

        is_dict = type_parser.is_dict(data)
        dataclass_fields: Dict[str, Field] = getattr(target, _DATACLASS_FIELDS_NAME, {})
        for field_name, field in dataclass_fields.items():
            value = self._get_value(data, is_dict, field_name, field)

            """数据为必填项"""
            if value is None and field.required:
                raise ValueError(f"{field_name} 为必填项")

            """反序列化过程中类型如果不正确会进行强行转换"""
            if value is not None and not isinstance(value, field.annotation):
                value = self._validate_value(value, field.annotation)

            setattr(instance, field_name, value)

        return instance  # type: ignore

    @staticmethod
    def _get_value(data: Union[dict, object], is_dict: bool, field_name: str, field: Field) -> Any:
        try:
            value = data.__getitem__(field_name) if is_dict else getattr(data, field_name)
        except (KeyError, AttributeError):
            value = field.get_default_value()
        return value

    def _validate_value(self, value, target_type):
        """内置验证器会尝试帮你转换类型，如果不成功将抛出异常"""
        # 基本数据类型验证器
        if target_type in self.__base_validators__:
            return self.__base_validators__[target_type].validate(value)
        elif type_parser.issubclass_safe(target_type, enum.Enum):
            return EnumValidator(target_enum=target_type).validate(value)
        elif type_parser.is_tuple(target_type):
            return TupleValidator()
        raise NotImplementedError(f"类型 {_format_type(target_type)} 未被支持")