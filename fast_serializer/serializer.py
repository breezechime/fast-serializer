# -*- coding:utf-8 -*-
import collections.abc
import copy
import datetime
import decimal
import enum
import uuid
import warnings
from abc import ABC
from typing import Dict, Any, Union, List, Callable, Generator, Optional, get_args, Literal, Tuple, Mapping, Set, \
    FrozenSet, Type
from .constants import _DATACLASS_FIELDS_NAME, _POST_INIT_NAME, SerMode, _T
from .exceptions import (ErrorDetail, ValidationError, SerializationError, SerializerBuildingError,
                         SerializationValueError)
from .field import Field
from .type_parser import type_parser
from .types import optional, DeserializeError, SerializeError
from .utils import isinstance_safe, _format_type, issubclass_safe, get_sub_serializer_kwargs
from .validator import validate_iter_with_catch


class FastDeserializer:
    """快速反序列化器"""

    name: str
    fast_dataclass: Type[_T]
    fields: Dict[str, Field]

    def __init__(self, dataclass: Type[_T], fields: optional[Dict[str, Field]] = None):
        self.dataclass = dataclass
        self.name = dataclass.__name__
        self.fields = fields or getattr(dataclass, _DATACLASS_FIELDS_NAME, {})

    def deserialize(self, input: Union[dict, object], errors: DeserializeError = 'strict', context: optional[Any] = None,
                    instance: _T = None) -> _T:
        """反序列化"""
        if instance is None:
            instance: _T = self.dataclass.__new__(self.dataclass)  # type: ignore

        self.deserialize_init(input, instance, errors)

        # post_init
        self.call_post_init(instance, context)
        return instance

    def deserialize_init(self, input: Union[dict, object], instance: _T, errors: DeserializeError = 'strict'):
        is_dict: bool = isinstance_safe(input, dict)
        errs: List[ErrorDetail] = []
        field_name: str
        field: Field
        for field_name, field in self.fields.items():
            try:
                field_value = input[field_name] if is_dict else getattr(input, field_name)
            except (KeyError, AttributeError):
                # missing use field default
                field_value = field.get_default_value()
            if field_value is None and field.required:
                errs.append(ErrorDetail([field_name], input, 'missing', '字段为必填项'))
                continue
            elif field_value is not None:
                field_value = validate_iter_with_catch(field_value, field.validator, [field_name], errs)

            setattr(instance, field_name, field_value)
        if errs and errors != 'ignore':
            raise ValidationError(title=self.name, line_errors=errs)

    @staticmethod
    def call_post_init(instance: _T, context: optional[Any] = None):
        if hasattr(instance, _POST_INIT_NAME):
            getattr(instance, _POST_INIT_NAME)(context)


class SerCheck(enum.Enum):

    NONE = 1

    ENABLED = 2

    LAX = 3


class SerParameter:
    """序列化参数"""

    mode: SerMode
    error_messages: List[str]
    by_alias: bool
    exclude_unset: bool
    exclude_none: bool
    fallback: optional[Callable]
    context: optional[Any]
    exclude: optional[dict]
    include: optional[dict]
    errors: SerializeError
    check: SerCheck

    __slots__ = ('mode', 'error_messages', 'by_alias', 'exclude_unset', 'exclude_none', 'context',
                 'fallback', 'exclude', 'include', 'errors', 'check')

    def __init__(
        self,
        mode: SerMode = SerMode.python,
        by_alias: bool = True,
        exclude_unset: bool = False,
        exclude_none: bool = False,
        fallback: optional[Callable] = None,
        context: optional[Any] = None,
        exclude: optional[dict] = None,
        include: optional[dict] = None,
        errors: SerializeError = 'warn',
    ):
        self.mode = mode
        self.by_alias = by_alias
        self.exclude_unset = exclude_unset
        self.exclude_none = exclude_none
        self.fallback = fallback
        self.context = context
        self.exclude = exclude
        self.include = include
        self.errors = errors
        self.error_messages = []
        self.check = SerCheck.NONE

    def on_fallback(self, expect_type, value: Any, got_type):
        if value is None:
            return value
        elif self.check != SerCheck.NONE:
            raise SerializationValueError(f'检查异常已开启，此异常为序列化器异常，如果您看到此异常在序列化中发生请反馈到社区。')
        else:
            self.fallback_error(expect_type, got_type or type(value))

    def fallback_error(self, expect_type, got_type):
        message = f'预期为 `{_format_type(expect_type)}`，但实际为 `{_format_type(got_type)}` - 序列化值可能与预期不符'
        self.add_error_message(message)

    def add_error_message(self, message: str):
        self.error_messages.append(message)

    def check_error(self):
        if self.errors == 'ignore':
            return True
        enter = '\n  '
        error_msg = f"Fast serializer warnings:\n  {enter.join(self.error_messages)}"
        if self.error_messages and self.errors == 'error':
            raise SerializationError(error_msg)
        elif self.error_messages and self.errors == 'warn':
            warnings.warn(error_msg)


class FastFilter:
    """筛选"""

    include: set
    exclude: set

    def __init__(self, include: set, exclude: set):
        self.include = include
        self.exclude = exclude


class FastSerializer:
    """快速数据类序列化器"""

    name: str
    fast_dataclass: Type[_T]
    fields: Dict[str, Field]

    def __init__(self, dataclass: Type[_T], fields: optional[Dict[str, Field]] = None):
        self.dataclass = dataclass
        self.name = dataclass.__name__
        self.fields = fields or getattr(dataclass, _DATACLASS_FIELDS_NAME, {})

    def to_python(
        self,
        value,
        /,
        mode: str = 'python',
        include: list = None,
        exclude: list = None,
        by_alias: bool = True,
        exclude_none: bool = False,
        errors: SerializeError = 'warn',
        context: optional[Any] = None,
    ) -> dict:
        """序列化到Python对象，JSON模式为任意语言可识别的JSON dict"""
        dict_value: dict = value.__dict__
        out_dict: dict = {}
        ser_parameter = SerParameter(
            mode=SerMode(mode),
            by_alias=by_alias,
            include=include,
            exclude=exclude,
            exclude_none=exclude_none,
            context=context,
            errors=errors,
        )
        for field_name, field in self.fields.items():
            serialize_value = dict_value.get(field_name)
            if exclude_none and serialize_value is None:
                continue
            if mode == 'python':
                out_value = field.serializer.to_python(serialize_value, ser_parameter)
            else:
                out_value = field.serializer.serialize(serialize_value, ser_parameter)
            out_dict[field_name] = out_value

        # 将额外的dict加入序列化

        # 将计算字段加入序列化

        ser_parameter.check_error()
        return out_dict

    def to_json(self): ...

    # def _dataclass_to_python(self):


class Serializer(ABC):

    serializer_name: str
    annotation: type

    def __init__(self, **kwargs): ...

    @property
    def name(self) -> str:
        return self.serializer_name

    def to_python(self, value, parameter: SerParameter):
        if isinstance_safe(value, self.annotation):
            return self.uncheck_to_python(value, parameter)
        return serialize_any_to_python(value, parameter, self.annotation)

    def serialize(self, value, parameter: SerParameter):
        if isinstance_safe(value, self.annotation):
            return self.uncheck_serialize(value, parameter)
        return serialize_any_to_json_value(value, parameter, self.annotation)

    @classmethod
    def uncheck_to_python(cls, value, parameter: SerParameter):
        return value

    @classmethod
    def uncheck_serialize(cls, value, parameter: SerParameter):
        return value

    @classmethod
    def build(cls, annotation, **kwargs) -> 'Serializer':
        return cls(annotation=annotation, **kwargs)


class AnySerializer(Serializer):
    """任意类型序列化器"""

    serializer_name = 'any'
    annotation = Any

    def to_python(self, value, parameter: SerParameter) -> Any:
        return serialize_any_to_python(value, parameter)

    def serialize(self, value, parameter: SerParameter) -> Any:
        return serialize_any_to_json_value(value, parameter)

    @classmethod
    def uncheck_to_python(cls, value, parameter: SerParameter) -> Any:
        return serialize_any_to_python(value, parameter)

    @classmethod
    def uncheck_serialize(cls, value, parameter: SerParameter) -> Any:
        return serialize_any_to_json_value(value, parameter)


class StrSerializer(Serializer):
    """字符串序列化器"""

    serializer_name = 'str'
    annotation = str

    def to_python(self, value, parameter: SerParameter) -> str:
        return super().to_python(value, parameter)

    def serialize(self, value, parameter: SerParameter) -> str:
        return super().serialize(value, parameter)

    @classmethod
    def uncheck_to_python(cls, value, parameter: SerParameter) -> str:
        return super().uncheck_to_python(value, parameter)

    @classmethod
    def uncheck_serialize(cls, value, parameter: SerParameter) -> str:
        return super().uncheck_serialize(value, parameter)


class FloatSerializer(Serializer):
    """浮点数序列化器"""

    serializer_name = 'float'
    annotation = float

    def to_python(self, value, parameter: SerParameter) -> float:
        return super().to_python(value, parameter)

    def serialize(self, value, parameter: SerParameter) -> float:
        return super().serialize(value, parameter)

    @classmethod
    def uncheck_to_python(cls, value, parameter: SerParameter) -> float:
        return super().uncheck_to_python(value, parameter)

    @classmethod
    def uncheck_serialize(cls, value, parameter: SerParameter) -> float:
        return super().uncheck_serialize(value, parameter)


class IntegerSerializer(Serializer):
    """整数序列化器"""

    serializer_name = 'int'
    annotation = int

    def to_python(self, value, parameter: SerParameter) -> int:
        return super().to_python(value, parameter)

    def serialize(self, value, parameter: SerParameter) -> int:
        return super().serialize(value, parameter)

    @classmethod
    def uncheck_to_python(cls, value, parameter: SerParameter) -> int:
        return super().uncheck_to_python(value, parameter)

    @classmethod
    def uncheck_serialize(cls, value, parameter: SerParameter) -> int:
        return super().uncheck_serialize(value, parameter)


class BoolSerializer(Serializer):
    """布尔序列化器"""

    serializer_name = 'bool'
    annotation = bool

    def to_python(self, value, parameter: SerParameter) -> bool:
        return super().to_python(value, parameter)

    def serialize(self, value, parameter: SerParameter) -> bool:
        return super().serialize(value, parameter)

    @classmethod
    def uncheck_to_python(cls, value, parameter: SerParameter) -> bool:
        return super().uncheck_to_python(value, parameter)

    @classmethod
    def uncheck_serialize(cls, value, parameter: SerParameter) -> bool:
        return super().uncheck_serialize(value, parameter)


class DecimalSerializer(Serializer):
    """数值序列化器"""

    serializer_name = 'decimal'
    annotation = decimal.Decimal

    def to_python(self, value, parameter: SerParameter) -> decimal.Decimal:
        return super().to_python(value, parameter)

    def serialize(self, value, parameter: SerParameter) -> str:
        if isinstance_safe(value, self.annotation):
            return self.uncheck_serialize(value, parameter)
        return serialize_any_to_python(value, parameter)

    @classmethod
    def uncheck_to_python(cls, value, parameter: SerParameter) -> decimal.Decimal:
        return super().uncheck_to_python(value, parameter)

    @classmethod
    def uncheck_serialize(cls, value, parameter: SerParameter) -> str:
        return str(value)


class BytesSerializer(Serializer):
    """字节序列化器"""

    serializer_name = 'bytes'
    annotation = bytes

    def to_python(self, value, parameter: SerParameter) -> bytes:
        return super().to_python(value, parameter)

    def serialize(self, value, parameter: SerParameter) -> str:
        if isinstance(value, self.annotation):
            return self.uncheck_serialize(value, parameter)
        return serialize_any_to_python(value, parameter)

    @classmethod
    def uncheck_to_python(cls, value, parameter: SerParameter) -> bytes:
        return super().uncheck_to_python(value, parameter)

    @classmethod
    def uncheck_serialize(cls, value, parameter: SerParameter) -> str:
        return value.decode('utf-8')


class DatetimeSerializer(Serializer):
    """日期时间序列化器"""

    serializer_name = 'datetime'
    annotation = datetime.datetime

    def to_python(self, value, parameter: SerParameter) -> datetime.datetime:
        return super().to_python(value, parameter)

    def serialize(self, value, parameter: SerParameter) -> str:
        if isinstance(value, self.annotation):
            return self.uncheck_serialize(value, parameter)
        return serialize_any_to_python(value, parameter)

    @classmethod
    def uncheck_to_python(cls, value, parameter: SerParameter) -> datetime.datetime:
        return super().uncheck_to_python(value, parameter)

    @classmethod
    def uncheck_serialize(cls, value, parameter: SerParameter) -> str:
        return value.isoformat()


class DateSerializer(Serializer):
    """日期序列化器"""

    serializer_name = 'date'
    annotation = datetime.date

    def to_python(self, value, parameter: SerParameter) -> datetime.date:
        return super().to_python(value, parameter)

    def serialize(self, value, parameter: SerParameter) -> str:
        if isinstance(value, self.annotation):
            return self.uncheck_serialize(value, parameter)
        return serialize_any_to_python(value, parameter)

    @classmethod
    def uncheck_to_python(cls, value, parameter: SerParameter) -> datetime.date:
        return super().uncheck_to_python(value, parameter)

    @classmethod
    def uncheck_serialize(cls, value, parameter: SerParameter) -> str:
        return value.strftime("%Y-%m-%d")


class TimeSerializer(Serializer):
    """时间序列化器"""

    serializer_name = 'time'
    annotation = datetime.time

    def to_python(self, value, parameter: SerParameter) -> datetime.time:
        return super().to_python(value, parameter)

    def serialize(self, value, parameter: SerParameter) -> str:
        if isinstance(value, self.annotation):
            return self.uncheck_serialize(value, parameter)
        return serialize_any_to_python(value, parameter)

    @classmethod
    def uncheck_to_python(cls, value, parameter: SerParameter) -> datetime.time:
        return super().uncheck_to_python(value, parameter)

    @classmethod
    def uncheck_serialize(cls, value, parameter: SerParameter) -> str:
        return value.strftime("%H:%M:%S")


class TimeDeltaSerializer(Serializer):
    """增量序列化器"""

    serializer_name = 'timedelta'
    annotation = datetime.timedelta

    def to_python(self, value, parameter: SerParameter) -> datetime.datetime:
        return super().to_python(value, parameter)

    def serialize(self, value, parameter: SerParameter) -> str:
        if isinstance(value, self.annotation):
            return self.uncheck_serialize(value, parameter)
        return serialize_any_to_python(value, parameter)

    @classmethod
    def uncheck_to_python(cls, value, parameter: SerParameter) -> bytes:
        return super().uncheck_to_python(value, parameter)

    @classmethod
    def uncheck_serialize(cls, value, parameter: SerParameter) -> str:
        str_value = str(value)
        length = len(str_value)
        if length <= 8:
            return str_value
        else:
            hour = value.seconds // 3600
            minute = (value.seconds % 3600) // 60
            second = value.seconds % 60
            hour_text = f'{hour}H' if hour > 0 else ''
            minute_text = f'{minute}M' if minute > 0 else ''
            second_text = f'{second}S' if second > 0 else ''
            return str(f"{'-' if value.days < 0 else ''}P{abs(value.days)}DT{hour_text}{minute_text}{second_text}")


class UuidSerializer(Serializer):
    """uuid序列化器"""

    serializer_name = 'uuid'
    annotation = uuid.UUID

    def to_python(self, value, parameter: SerParameter) -> uuid.UUID:
        return super().to_python(value, parameter)

    def serialize(self, value, parameter: SerParameter) -> str:
        if isinstance(value, self.annotation):
            return self.uncheck_serialize(value, parameter)
        return serialize_any_to_python(value, parameter)

    @classmethod
    def uncheck_to_python(cls, value, parameter: SerParameter) -> uuid.UUID:
        return super().uncheck_to_python(value, parameter)

    @classmethod
    def uncheck_serialize(cls, value, parameter: SerParameter) -> str:
        return str(value)


class EnumSerializer(Serializer):
    """枚举序列化器"""

    serializer_name = 'enum'
    annotation = enum.Enum
    enum_class: enum.EnumType
    use_value: bool

    def __init__(self, enum_class: enum.EnumType, use_value: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.enum_class = enum_class
        self.use_value = use_value
        self.values = [i.value if self.use_value else i.name for i in self.enum_class]

    def to_python(self, value, parameter: SerParameter) -> enum.Enum:
        return super().to_python(value, parameter)

    def serialize(self, value, parameter: SerParameter) -> Any:
        if isinstance(value, self.annotation):
            return self.uncheck_serialize(value, parameter)
        return serialize_any_to_python(value, parameter)

    @classmethod
    def uncheck_to_python(cls, value, parameter: SerParameter) -> enum.Enum:
        return super().uncheck_to_python(value, parameter)

    @classmethod
    def uncheck_serialize(cls, value, parameter: SerParameter) -> Any:
        return serialize_any_to_json_value(value.value, parameter)

    @classmethod
    def build(cls, annotation: _T, **kwargs) -> 'EnumSerializer':
        return cls(annotation, **kwargs)


class IntEnumSerializer(Serializer):
    """整型枚举序列化器"""

    serializer_name = 'int_enum'
    annotation = enum.IntEnum
    enum_class: enum.EnumType
    use_value: bool

    def __init__(self, enum_class: enum.EnumType, use_value: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.enum_class = enum_class
        self.use_value = use_value
        self.values = [i.value if self.use_value else i.name for i in self.enum_class]

    def to_python(self, value, parameter: SerParameter) -> enum.IntEnum:
        return super().to_python(value, parameter)

    def serialize(self, value, parameter: SerParameter) -> int:
        if isinstance(value, self.annotation):
            return self.uncheck_serialize(value, parameter)
        return serialize_any_to_python(value, parameter)

    @classmethod
    def uncheck_to_python(cls, value, parameter: SerParameter) -> enum.IntEnum:
        return super().uncheck_to_python(value, parameter)

    @classmethod
    def uncheck_serialize(cls, value, parameter: SerParameter) -> int:
        return int(value.value)

    @classmethod
    def build(cls, annotation: _T, **kwargs) -> 'IntEnumSerializer':
        return cls(annotation, **kwargs)


class UnionSerializer(Serializer):
    """联合序列化器"""

    serializer_name = 'union'
    annotation = Union
    serializers: List[Serializer]

    def __init__(self, serializers: List[Serializer], **kwargs):
        super().__init__(**kwargs)
        self.serializers = serializers

    def to_python(self, value, parameter: SerParameter) -> Any:
        return super().to_python(value, parameter)

    def serialize(self, value, parameter: SerParameter) -> Any:
        new_ser_parameter = copy.copy(parameter)
        new_ser_parameter.check = SerCheck.ENABLED

        for serializer in self.serializers:
            try:
                return serializer.serialize(value, new_ser_parameter)
            except SerializationValueError:
                pass
        return serialize_any_to_python(value, parameter, self.name)

    @classmethod
    def uncheck_to_python(cls, value, parameter: SerParameter) -> enum.IntEnum:
        return super().uncheck_to_python(value, parameter)

    @classmethod
    def uncheck_serialize(cls, value, parameter: SerParameter) -> int:
        return int(value.value)

    @classmethod
    def build(cls, annotation: _T, **kwargs) -> 'UnionSerializer':
        args = get_args(annotation)
        if not args:
            raise SerializerBuildingError(f"使用Union注解至少需要有一种类型才可构建 {cls.__name__}")
        if not type_parser.is_union(annotation):
            raise SerializerBuildingError(f"输入应为Union注解才可构建 {cls.__name__}")
        serializers = [matching_serializer(sub, **get_sub_serializer_kwargs(kwargs, i)) for i, sub in enumerate(args)]
        return cls(serializers=serializers, **kwargs)

    @property
    def name(self) -> str:
        return str(f"{self.serializer_name}[{', '.join([ser.name for ser in self.serializers])}]")


class LiteralSerializer(Serializer):
    """字面量序列化器"""

    serializer_name = 'literal'
    annotation = Literal
    expected_values: Tuple[Any, ...]

    def __init__(self, *expected: Tuple[Any, ...], **kwargs):
        super().__init__(**kwargs)
        self.expected_values = expected

    def to_python(self, value, parameter: SerParameter) -> Union[int, str, bool, Any]:
        if value in self.expected_values:
            return self.uncheck_to_python(value, parameter)
        return serialize_any_to_python(value, parameter, self.name)

    def serialize(self, value, parameter: SerParameter) -> Union[int, str, bool, Any]:
        if value in self.expected_values:
            return self.uncheck_serialize(value, parameter)
        return serialize_any_to_json_value(value, parameter, self.name)

    @classmethod
    def uncheck_to_python(cls, value, parameter: SerParameter) -> Union[int, str, bool, Any]:
        return super().uncheck_to_python(value, parameter)

    @classmethod
    def uncheck_serialize(cls, value, parameter: SerParameter) -> Union[int, str, bool, Any]:
        return super().uncheck_serialize(value, parameter)

    @classmethod
    def build(cls, annotation, **kwargs):
        if not type_parser.is_literal(annotation):
            raise ValueError(f"输入应为Literal注解才可构建 {cls.__name__}")
        args = get_args(annotation)
        return cls(*args)

    @property
    def name(self) -> str:
        return str(f'{self.serializer_name}[{", ".join([f"{value!r}" for value in self.expected_values])}]')


class DictSerializer(Serializer):
    """字典序列化器"""

    serializer_name = 'dict'
    annotation = dict
    key_serializer: Serializer
    value_serializer: Serializer

    def __init__(self, key_serializer: Serializer, value_serializer: Serializer, **kwargs):
        super().__init__(**kwargs)
        self.key_serializer = key_serializer
        self.value_serializer = value_serializer

    def to_python(self, value, parameter: SerParameter) -> dict:
        if not isinstance_safe(value, self.annotation):
            return serialize_any_to_python(value, parameter, self.name)
        out_dict = dict()
        for key, dict_value in value.items():
            key_value = self.value_serializer.to_python(key, parameter)
            serialize_value = self.value_serializer.to_python(dict_value, parameter)
            out_dict[key_value] = serialize_value
        return out_dict

    def serialize(self, value, parameter: SerParameter) -> dict:
        if not isinstance_safe(value, self.annotation):
            return serialize_any_to_json_value(value, parameter, self.name)
        out_dict = dict()
        for key, dict_value in value.items():
            key_value = self.key_serializer.serialize(key, parameter)
            serialize_value = self.value_serializer.serialize(dict_value, parameter)
            out_dict[key_value] = serialize_value
        return out_dict

    @classmethod
    def uncheck_to_python(cls, value, parameter: SerParameter) -> dict:
        out_dict = dict()
        for key, dict_value in value.items():
            key_value = serialize_any_to_python(key, parameter)
            serialize_value = serialize_any_to_python(dict_value, parameter)
            out_dict[key_value] = serialize_value
        return out_dict

    @classmethod
    def uncheck_serialize(cls, value, parameter: SerParameter) -> dict:
        out_dict = dict()
        for key, dict_value in value.items():
            key_value = serialize_any_to_json_value(key, parameter)
            serialize_value = serialize_any_to_json_value(dict_value, parameter)
            out_dict[key_value] = serialize_value
        return out_dict

    @classmethod
    def build(cls, annotation: _T, **kwargs) -> 'DictSerializer':
        annotation_args = get_args(annotation)
        args_length = len(annotation_args)
        key_validator = matching_serializer(annotation_args[0], **get_sub_serializer_kwargs(kwargs, 0)) if (
                args_length >= 1) else GLOBAL_SERIALIZERS[Any]
        value_validator = matching_serializer(annotation_args[1], **get_sub_serializer_kwargs(kwargs, 1)) if (
                args_length >= 2) else GLOBAL_SERIALIZERS[Any]
        return cls(key_validator, value_validator, **kwargs)

    @property
    def name(self) -> str:
        return str(f'{self.serializer_name}[{self.key_serializer.name}, {self.value_serializer.name}]')


class ListSerializer(Serializer):
    """列表序列化器"""

    serializer_name = 'list'
    annotation = list
    item_serializer: Serializer

    def __init__(self, item_serializer: Serializer, **kwargs):
        super().__init__(**kwargs)
        self.item_serializer = item_serializer

    def to_python(self, value, parameter: SerParameter) -> list:
        return [self.item_serializer.to_python(item, parameter) for item in value]

    def serialize(self, value, parameter: SerParameter) -> list:
        return [self.item_serializer.serialize(item, parameter) for item in value]

    @classmethod
    def uncheck_to_python(cls, value, parameter: SerParameter) -> list:
        return [serialize_any_to_python(value, parameter) for value in value]

    @classmethod
    def uncheck_serialize(cls, value, parameter: SerParameter) -> list:
        return [serialize_any_to_json_value(value, parameter) for value in value]

    @classmethod
    def build(cls, annotation: _T, **kwargs) -> 'ListSerializer':
        args = get_args(annotation)
        sub_annotation = args[0] if args else Any
        item_serializer = matching_serializer(sub_annotation, **get_sub_serializer_kwargs(kwargs))
        return cls(item_serializer=item_serializer, **kwargs)


class SetSerializer(Serializer):
    """集合序列化器"""

    serializer_name = 'set'
    annotation = set
    item_serializer: Serializer

    def __init__(self, item_serializer: Serializer, **kwargs):
        super().__init__(**kwargs)
        self.item_serializer = item_serializer

    def to_python(self, value, parameter: SerParameter) -> set:
        return set((self.item_serializer.to_python(item, parameter) for item in value))

    def serialize(self, value, parameter: SerParameter) -> list:
        return [self.item_serializer.serialize(item, parameter) for item in value]

    @classmethod
    def uncheck_to_python(cls, value, parameter: SerParameter) -> set:
        return set((serialize_any_to_python(value, parameter) for value in value))

    @classmethod
    def uncheck_serialize(cls, value, parameter: SerParameter) -> list:
        return [serialize_any_to_json_value(value, parameter) for value in value]


class FrozenSetSerializer(Serializer):
    """冻结集合序列化器"""

    serializer_name = 'frozenset'
    annotation = frozenset
    item_serializer: Serializer

    def __init__(self, item_serializer: Serializer, **kwargs):
        super().__init__(**kwargs)
        self.item_serializer = item_serializer

    def to_python(self, value, parameter: SerParameter) -> frozenset:
        return frozenset((self.item_serializer.to_python(item, parameter) for item in value))

    def serialize(self, value, parameter: SerParameter) -> list:
        return [self.item_serializer.serialize(item, parameter) for item in value]

    @classmethod
    def uncheck_to_python(cls, value, parameter: SerParameter) -> frozenset:
        return frozenset((serialize_any_to_python(value, parameter) for value in value))

    @classmethod
    def uncheck_serialize(cls, value, parameter: SerParameter) -> list:
        return [serialize_any_to_json_value(value, parameter) for value in value]


class TupleSerializer(Serializer):
    """元祖序列化器"""

    serializer_name = 'tuple'
    annotation = tuple
    serializers: List[Serializer]
    variadic: bool = True
    accept_annotations: tuple = (tuple, list, set, frozenset)

    def __init__(self, serializers: List[Serializer], variadic: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.serializers = serializers
        self.variadic = variadic

    def to_python(self, value, parameter: SerParameter) -> tuple:
        if not isinstance_safe(value, self.accept_annotations):
            return serialize_any_to_python(value, parameter, self.name)
        self.check_variadic(value, parameter)
        out_list: list = []
        if not self.variadic:
            for index, item_value in enumerate(value):
                try:
                    serialize_value = self.serializers[index].to_python(item_value, parameter)
                except IndexError:
                    serialize_value = serialize_any_to_python(item_value, parameter)
                out_list.append(serialize_value)
            return tuple(out_list)
        # 可变
        serializer = self.serializers[0]
        return tuple(serializer.to_python(value, parameter) for value in value)

    def serialize(self, value, parameter: SerParameter) -> list:
        if not isinstance_safe(value, self.accept_annotations):
            return serialize_any_to_python(value, parameter, self.name)
        self.check_variadic(value, parameter)
        out_list: list = []
        if not self.variadic:
            for index, item_value in enumerate(value):
                try:
                    serialize_value = self.serializers[index].serialize(item_value, parameter)
                except IndexError:
                    serialize_value = serialize_any_to_json_value(item_value, parameter)
                out_list.append(serialize_value)
            return out_list
        # 可变
        serializer = self.serializers[0]
        return [serializer.serialize(value, parameter) for value in value]

    @classmethod
    def uncheck_to_python(cls, value, parameter: SerParameter) -> tuple:
        return tuple((serialize_any_to_python(value, parameter) for value in value))

    @classmethod
    def uncheck_serialize(cls, value, parameter: SerParameter) -> list:
        return [serialize_any_to_json_value(value, parameter) for value in value]

    @classmethod
    def build(cls, annotation: _T, **kwargs) -> 'TupleSerializer':
        args = get_args(annotation)
        if Ellipsis in args:
            variadic = True
            args = list(args)
            args.remove(Ellipsis)
        else:
            variadic = False
        serializers = [matching_serializer(sub, **get_sub_serializer_kwargs(kwargs, i))
                       for i, sub in enumerate(args)]
        if not serializers:
            serializers = [GLOBAL_SERIALIZERS[Any]]
            variadic = True
        if variadic and len(serializers) > 1:
            raise SerializerBuildingError(f'可变元组只能有一种类型')
        return cls(serializers=serializers, variadic=variadic, **kwargs)

    @property
    def name(self) -> str:
        return str(f'{self.serializer_name}[{", ".join([ser.name for ser in self.serializers])}]')

    def check_variadic(self, value, parameter: SerParameter) -> bool:
        if not self.variadic and len(value) > len(self.serializers):
            parameter.add_error_message('元组中存在意外的额外项')
            return False
        return True


class OptionalSerializer(Serializer):
    """可空序列化器"""

    serializer_name = 'optional'
    annotation = Optional
    serializer: Serializer

    def __init__(self, serializer: Serializer, **kwargs):
        super().__init__(**kwargs)
        self.serializer = serializer

    def to_python(self, value, parameter: SerParameter) -> Optional[Any]:
        if value is None:
            return value
        return self.serializer.to_python(value, parameter)

    def serialize(self, value, parameter: SerParameter) -> Optional[Any]:
        if value is None:
            return value
        return self.serializer.serialize(value, parameter)

    @classmethod
    def uncheck_to_python(cls, value, parameter: SerParameter):
        return None

    @classmethod
    def uncheck_serialize(cls, value, parameter: SerParameter):
        return None

    @classmethod
    def build(cls, annotation: _T, **kwargs):
        if not type_parser.is_optional(annotation) or annotation == Any:
            annotation = Optional[annotation]
        serializer = matching_serializer(get_args(annotation)[0], **kwargs)
        return cls(serializer=serializer, **kwargs)


class GeneratorSerializer(Serializer):
    """生成器序列化器"""

    serializer_name = 'generator'
    annotation = Generator

    def to_python(self, value, parameter: SerParameter) -> uuid.UUID:
        return super().to_python(value, parameter)

    def serialize(self, value, parameter: SerParameter) -> str:
        if isinstance(value, self.annotation):
            return self.uncheck_serialize(value, parameter)
        return serialize_any_to_python(value, parameter)

    @classmethod
    def uncheck_to_python(cls, value, parameter: SerParameter) -> uuid.UUID:
        return super().uncheck_to_python(value, parameter)

    @classmethod
    def uncheck_serialize(cls, value, parameter: SerParameter) -> str:
        return str(value)


GLOBAL_SERIALIZERS: dict = {
    Any: AnySerializer(),
    str: StrSerializer(),
    int: IntegerSerializer(),
    float: FloatSerializer(),
    bool: BoolSerializer(),
    bytes: BytesSerializer(),
    decimal.Decimal: DecimalSerializer(),
}

MATCH_SERIALIZERS: dict = {
    Any: AnySerializer,
    str: StrSerializer,
    int: IntegerSerializer,
    float: FloatSerializer,
    bool: BoolSerializer,
    bytes: BytesSerializer,
    decimal.Decimal: DecimalSerializer,
    datetime.datetime: DatetimeSerializer,
    datetime.date: DateSerializer,
    datetime.time: TimeSerializer,
    datetime.timedelta: TimeDeltaSerializer,
    Optional: OptionalSerializer,
    uuid.UUID: UuidSerializer,
    enum.Enum: EnumSerializer,
    enum.IntEnum: IntEnumSerializer,
    Union: UnionSerializer,
    Literal: LiteralSerializer,
    dict: DictSerializer,
    Dict: DictSerializer,
    Mapping: DictSerializer,
    list: ListSerializer,
    List: ListSerializer,
    set: SetSerializer,
    Set: SetSerializer,
    frozenset: FrozenSetSerializer,
    FrozenSet: FrozenSetSerializer,
    tuple: TupleSerializer,
    Tuple: TupleSerializer,
    Generator: GeneratorSerializer,
    collections.abc.Generator: GeneratorSerializer,
}


def matching_serializer(annotation, **kwargs):
    """匹配序列化器"""
    origin_annotation = type_parser.get_origin_safe(annotation) or annotation
    # 如何未指定kwargs尝试在全局序列化器中查找（省内存）
    if not kwargs:
        try:
            return GLOBAL_SERIALIZERS[origin_annotation]
        except KeyError:
            pass
    try:
        return MATCH_SERIALIZERS[origin_annotation].build(annotation, **kwargs)
    except KeyError:
        # 特殊注解
        if issubclass_safe(annotation, enum.IntEnum):
            return MATCH_SERIALIZERS[enum.IntEnum].build(annotation, **kwargs)
        elif issubclass_safe(annotation, enum.Enum):
            return MATCH_SERIALIZERS[enum.Enum].build(annotation, **kwargs)
    raise SerializerBuildingError(f'无法为 {annotation} 类型构建序列化器')


def serialize_any_to_python(value, parameter: SerParameter, expect_type: Union[type, str] = None) -> Any:
    """序列化任意数据到python对象"""
    if expect_type:
        parameter.on_fallback(expect_type, value, type(value))
    try:
        return MATCH_SERIALIZERS[type(value)].uncheck_to_python(value, parameter)
    except KeyError:
        # errs
        return value


def serialize_any_to_json_value(value, parameter: SerParameter, expect_type: Union[type, str] = None) -> Any:
    """序列化任意数据到任意语言可理解对象，并且可解析到json输出到文件"""
    if expect_type:
        parameter.on_fallback(expect_type, value, type(value))
    try:
        return MATCH_SERIALIZERS[type(value)].uncheck_serialize(value, parameter)
    except KeyError:
        # errs
        return value