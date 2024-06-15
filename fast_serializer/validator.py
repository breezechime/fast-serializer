# -*- coding:utf-8 -*-
import datetime
import enum
import re
import time
import uuid
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any, Deque, Generator, Union, Collection, Iterable, Literal, NoReturn, List, get_args, Tuple
from .constants import _T
from .type_parser import type_parser
from .types import optional
from .utils import _format_type


class Validator(ABC):
    """验证器基类"""

    name: str
    annotation: _T

    @abstractmethod
    def validate(self, value, **kwargs) -> NoReturn:
        """验证数据并返回正确数据或抛出异常"""
        raise NotImplementedError('必须实现验证方法')

    def is_instance(self, value, annotation=None) -> bool:
        annotation = annotation or self.annotation
        return type_parser.isinstance_safe(value, annotation)

    def get_name(self) -> str:
        return self.name

    def __repr__(self):
        return f"{self.__class__.__name__}(\n\tname: {self.name},\n\tannotation: {self.annotation}\n)"

    @classmethod
    def build(cls, annotation: _T, *args, **kwargs) -> 'Validator':
        return cls()


class AnyValidator(Validator):
    """任意类型验证器"""

    name = 'any'
    annotation = Any

    def validate(self, value, **kwargs):
        return value


class StringValidator(Validator):
    """字符串验证器"""

    name = 'str'
    annotation = str

    def validate(self, value, allow_number: bool = True, **kwargs) -> str:
        maybe_str = self.maybe_str(value)
        if maybe_str:
            return maybe_str
        elif type_parser.isinstance_safe(value, bytearray):
            return value.decode('utf-8')
        numbers_types = (IntegerValidator.annotation, FloatValidator.annotation,
                         DecimalValidator.annotation, BoolValidator.annotation)
        if allow_number and type_parser.isinstance_safe(value, numbers_types):
            return self.annotation(value)

        raise ValueError('Input should be string')

    @classmethod
    def maybe_str(cls, value, raise_error: bool = True) -> optional[str]:
        if type_parser.isinstance_safe(value, cls.annotation):
            return value
        elif type_parser.isinstance_safe(value, BytesValidator.annotation):
            try:
                return value.decode('utf-8')
            except UnicodeDecodeError:
                if not raise_error:
                    return False
                raise ValueError('Input should be string')
        return None


class BoolValidator(Validator):
    """布尔验证器"""

    name = 'bool'
    annotation = bool

    def validate(self, value, **kwargs) -> bool:
        if type_parser.isinstance_safe(value, self.annotation):
            return value
        elif type_parser.isinstance_safe(value, IntegerValidator.annotation):
            return self.int_to_bool(value)
        elif type_parser.isinstance_safe(value, FloatValidator.annotation):
            return self.int_to_bool(IntegerValidator.annotation(value))
        elif type_parser.isinstance_safe(value, StringValidator.annotation):
            return self.str_to_bool(value)

        raise ValueError('Input should be bool')

    @staticmethod
    def str_to_bool(value: str) -> bool:
        if value.lower() in ['0', 'false', 'f', 'n', 'no', 'off']:
            return False
        elif value.lower() in ['1', 'true', 't', 'y', 'yes', 'on']:
            return True

        raise ValueError('Input should be bool')

    @staticmethod
    def int_to_bool(value: int) -> bool:
        if value == 0:
            return False
        elif value == 1:
            return True

        raise ValueError('Input should be bool')


class IntegerValidator(Validator):
    """整型验证器"""

    name = 'int'
    annotation = int

    def validate(self, value, **kwargs):
        if type_parser.isinstance_safe(value, self.annotation):
            return value
        elif type_parser.isinstance_safe(value, BoolValidator.annotation):
            return self.bool_to_int(value)
        elif type_parser.isinstance_safe(value, FloatValidator.annotation):
            return self.float_to_int(value)
        elif type_parser.isinstance_safe(value, DecimalValidator.annotation):
            return self.decimal_to_int(value)
        maybe_str = StringValidator.maybe_str(value)
        if maybe_str:
            return self.str_to_int(value)
        elif type_parser.isinstance_safe(value, enum.Enum):
            return self.enum_to_int(value)

        raise ValueError('Input should be integer')

    @staticmethod
    def bool_to_int(value: bool):
        return int(value)

    @staticmethod
    def str_to_int(value: str):
        return int(value)

    @staticmethod
    def float_to_int(value: float):
        return int(value)

    @staticmethod
    def decimal_to_int(value: float):
        return int(value)

    @staticmethod
    def enum_to_int(value: enum.Enum):
        return int(value.value)


class FloatValidator(Validator):
    """浮点验证器"""

    name = 'float'
    annotation = float

    def validate(self, value, **kwargs):
        if type_parser.isinstance_safe(value, self.annotation):
            return value
        elif type_parser.isinstance_safe(value, IntegerValidator.annotation):
            return self.annotation(value)
        elif type_parser.isinstance_safe(value, DecimalValidator.annotation):
            return self.annotation(value)
        maybe_str = StringValidator.maybe_str(value)
        if maybe_str:
            return self.annotation(value)

        raise ValueError('Input should be float')


class DecimalValidator(FloatValidator):
    """Decimal验证器"""

    name = 'decimal'
    annotation = Decimal

    def validate(self, value, **kwargs):
        if self.is_instance(value, self.annotation):
            return value
        elif type_parser.isinstance_safe(value, IntegerValidator.annotation):
            return self.annotation(value)
        elif type_parser.isinstance_safe(value, FloatValidator.annotation):
            return self.annotation(value)
        maybe_str = StringValidator.maybe_str(value)
        if maybe_str:
            return self.annotation(value)

        raise ValueError('Input should be decimal')


class BytesValidator(Validator):
    """字节验证器"""

    name = 'bytes'
    annotation = bytes

    def validate(self, value, **kwargs):
        if type_parser.isinstance_safe(value, self.annotation):
            return value
        elif type_parser.isinstance_safe(value, StringValidator.annotation):
            return value.encode('utf-8')
        elif type_parser.isinstance_safe(value, bytearray):
            return self.annotation(value)


class TargetTypeValidator(Validator):
    """目标类型验证器"""

    name = 'target_type'

    def __init__(self, annotation: _T):
        self.annotation = annotation
        self.name = _format_type(annotation)

    def validate(self, value, **kwargs):
        if type_parser.isinstance_safe(value, self.annotation):
            return value
        raise ValueError(f'输入应为`{self.name}`类型')


class OptionalValidator(Validator):
    """可空类型验证器"""

    name = 'optional'
    annotation = optional
    validator: Validator

    def validate(self, value, **kwargs):
        if value is None:
            return value
        return self.validator.validate(value)

    @classmethod
    def build(cls, annotation: _T, *args, **kwargs):
        if not type_parser.is_optional(annotation):
            raise ValueError(f"输入应为Optional注解才可构建 {cls.__name__}")
        target_validator = matching_validator(get_args(annotation)[0])
        validator = cls()
        validator.validator = target_validator
        return validator


class UnionValidator(Validator):
    """联合类型验证器"""

    name = 'union'
    annotation = Union
    validators: List[Validator] = []

    def validate(self, value, **kwargs):
        error = None
        for validator in self.validators:
            try:
                return validator.validate(value)
            except (Exception,) as e:
                error = e
                continue
        raise error

    @classmethod
    def build(cls, annotation: _T, *args, **kwargs):
        if not type_parser.is_union(annotation):
            raise ValueError(f"输入应为Union注解才可构建 {cls.__name__}")
        validator = cls()
        validator.validators = [matching_validator(ann) for ann in get_args(annotation)]
        return validator


class LiteralValidator(Validator):
    """字面量类型验证器"""

    name = 'literal'
    annotation = Literal
    expected_values: Tuple[Any, ...]

    def __init__(self, *expected: Tuple[Any, ...]):
        self.expected_values = expected
        self.update_validator()

    def validate(self, value, **kwargs):
        if value in self.expected_values:
            return value
        raise ValueError(f'输入应为 {self.format_expected_values}')

    @classmethod
    def build(cls, annotation, *args, **kwargs):
        if not type_parser.is_literal(annotation):
            raise ValueError(f"输入应为Literal注解才可构建 {cls.__name__}")

        args = get_args(annotation)
        return cls(*args)

    def __repr__(self):
        return (f"{self.__class__.__name__}("
                f"\n\tname: {self.name}"
                f"\n\tannotation: {self.annotation}"
                f"\n\tvalues: {self.expected_values}\n"
                f")")

    def update_validator(self):
        self.name = f'literal[{",".join([f"{value!r}" for value in self.expected_values])}]'

    @property
    def format_expected_values(self):
        return f'{", ".join([f"`{value!r}`" for value in self.expected_values])}'


# TODO
class FastDataclassValidator(Validator):
    """快速数据类验证器"""

    def validate(self, value, **kwargs):
        pass


class PydanticModelValidator(Validator):
    """Pydantic模型验证器"""

    def validate(self, value, **kwargs):
        try:
            from pydantic import BaseModel
        except ImportError:
            raise ImportError('导入Pydantic失败, 可能未安装')
        if type_parser.issubclass_safe(value, BaseModel):
            return value
        raise ValueError('输入应为Pydantic模型')


class DataclassValidator(Validator):
    """数据类验证器"""

    name = 'dataclass'

    def validate(self, value, **kwargs):
        try:
            from dataclasses import is_dataclass
        except ImportError:
            raise ImportError('导入Dataclass失败, 您把它删了吗？')
        if is_dataclass(value):
            return value
        raise ValueError('输入应为Dataclass数据类')


# TODO
class DictValidator(Validator):
    """字典验证器"""

    name = 'dict'
    annotation = dict
    key_validator: Validator
    value_validator: Validator

    def validate(self, value, **kwargs):
        pass


class TypedDictField:
    name: str
    required: bool


# TODO
class TypedDictValidator(Validator):
    """带类型字典验证器"""

    def validate(self, value, **kwargs):
        pass


# TODO
class IterableValidator(Validator):
    """可迭代验证器"""

    name = 'iterable'
    annotation = Iterable
    item_validator: Validator
    min_length: optional[int]
    max_length: optional[int]

    def __init__(self, item_validator):
        self.item_validator = item_validator or AnyValidator()

    def validate(self, value, **kwargs):
        if type_parser.is_iterable(value):
            return value
        raise ValueError('输入应为可迭代类型')

    @classmethod
    def extract_iterable(cls, value: Iterable):
        if type_parser.is_list(value):
            return value
        elif type_parser.is_tuple(value):
            return value


# TODO
class ListValidator(Validator):
    """列表验证器"""

    name = 'list'
    annotation = list
    item_validator: Validator
    min_length: optional[int]
    max_length: optional[int]

    def __init__(self, item_validator):
        self.item_validator = item_validator or AnyValidator()

    def validate(self, value, **kwargs):
        is_list = type_parser.isinstance_safe(value, list)
        if not is_list and not (type_parser.issubclass_safe(value, Iterable) or type_parser.issubclass_safe(value, Collection)):
            raise ValueError('输入应为列表类型')
        # 验证子元素
        return [self.item_validator.validate(item) for item in value]


# TODO
class TupleValidator(Validator):
    """元组验证器"""

    name = 'tuple'
    annotation = tuple
    item_validators: List[Validator]
    min_length: optional[int]
    max_length: optional[int]

    def __init__(self, item_validators: List[Validator]):
        self.item_validators = item_validators or []

    def validate(self, value, **kwargs):
        if not type_parser.is_tuple(value):
            return ValueError('输入应为元组类型')

        for validator in self.item_validators:
            validator.validate(value)

    @classmethod
    def build(cls, annotation: _T, *args, **kwargs):
        if type_parser.is_iterable(annotation):
            raise ValueError(f"输入应为可迭代类型注解才可构建 {cls.__name__}")

        # return cls()


# TODO
class SetValidator(Validator):
    """集合验证器"""

    def validate(self, value, **kwargs):
        self.item_validator: Validator


# TODO
class FrozenValidator(Validator):
    """冻结集合验证器"""

    name = 'frozenset'
    annotation = frozenset

    def validate(self, value, **kwargs):
        self.item_validator: Validator


# TODO
class GeneratorValidator(Validator):
    """生成器验证器"""

    name = 'generator'
    annotation = Generator

    def validate(self, value, **kwargs):
        self.item_validator: Validator


# TODO
class CallValidator(Validator):

    def validate(self, value, **kwargs):
        pass


# TODO
class CallableValidator(Validator):

    def validate(self, value, **kwargs):
        pass


class DatetimeValidator(Validator):
    """日期时间验证器"""

    name = 'datetime'
    annotation = datetime.datetime

    """年长度"""
    year_length = len(StringValidator.annotation(datetime.MAXYEAR))
    """月长度"""
    month_length = 2
    """日长度"""
    day_length = 2
    """总长度"""
    date_length = year_length + month_length + day_length
    """时间戳容忍值"""
    tolerance_value = 100
    """对比时间戳"""
    compare_timestamp = time.time()
    """时间戳长度"""
    timestamp_length = len(StringValidator.annotation(int(compare_timestamp)))

    def validate(self, value, **kwargs):
        if type_parser.isinstance_safe(value, self.annotation):
            return value
        elif type_parser.isinstance_safe(value, (IntegerValidator.annotation, FloatValidator.annotation,
                                                 StringValidator.annotation)):
            return self.str_or_int_to_datetime(value)
        elif type_parser.isinstance_safe(value, DateValidator.annotation):
            return self.date_to_datetime(value)
        raise ValueError('输入应为有效日期时间类型')

    @classmethod
    def timestamp_to_datetime(cls, value: Union[int, float]) -> datetime.datetime:
        # 兼容毫秒级时间戳 下方为了兼容'1718245600000.0' 这种字符串带小数点的情况无法直接int
        if len(str(int(float(value)))) > cls.timestamp_length:
            value = value / 1000
        return datetime.datetime.fromtimestamp(value)

    @classmethod
    def date_to_datetime(cls, value: datetime.date) -> datetime.datetime:
        return datetime.datetime(year=value.year, month=value.month, day=value.day)

    @classmethod
    def str_or_int_to_datetime(cls, value: Union[str, int]):
        value = StringValidator.annotation(value)
        length = len(value)
        if length < cls.year_length:
            raise ValueError('输入应为有效日期类型')
        int_value = None
        try:
            int_value = int(float(value))  # 兼容'2024.0'
        except (ValueError, TypeError):
            pass
        if int_value and int_value < datetime.MAXYEAR:
            # e.g: 2024 4位最短
            return datetime.datetime(int_value, 1, 1)
        elif length == cls.date_length and int_value:
            # e.g: 20240204 8位无符号版本
            year = int(value[:cls.year_length])
            month = int(value[cls.year_length:6])
            day = int(value[cls.year_length + 2:])
            return datetime.datetime(year, month, day)
        elif length == cls.date_length + 2 and int_value:
            # e.g: 1718245600 时间戳10位版本
            return datetime.datetime.fromtimestamp(int_value)
        elif length == cls.date_length + 2 and int_value is None:
            # e.g: 2024-02-04 10位版本
            delimiter = cls.get_delimiter(value)
            return datetime.datetime.strptime(value, f'%Y{delimiter}%m{delimiter}%d')
        elif length == cls.date_length + 5 and int_value:
            # e.g: 1718245600000 时间戳13位版本
            return cls.timestamp_to_datetime(int_value)
        elif cls.date_length + 10 >= length >= cls.date_length + 6 and int_value:
            # e.g: 17182456.000 时间戳14-18位版本
            return cls.timestamp_to_datetime(int_value)
        elif length == cls.date_length + 8 and int_value is None:
            # e.g: 2024-02-04 10:15 16位版本
            delimiter = cls.get_delimiter(value)
            return datetime.datetime.strptime(value, f'%Y{delimiter}%m{delimiter}%d %H:%M')
        elif length == cls.date_length + 11 and int_value is None and 'T' not in value:
            # e.g: 2024-02-04 10:15:30
            delimiter = cls.get_delimiter(value)
            return datetime.datetime.strptime(value, f'%Y{delimiter}%m{delimiter}%d %H:%M:%S')
        elif length >= cls.date_length + 11 and int_value is None:
            # rfc3339格式支持
            return datetime.datetime.fromisoformat(value)
        raise ValueError('输入应为有效日期时间类型')

    @staticmethod
    def get_delimiter(value: str):
        return '/' if '/' in value else '.' if '.' in value else '-'


class TimeValidator(Validator):
    """时间验证器"""

    name = 'time'
    annotation = datetime.time

    def validate(self, value, **kwargs):
        if type_parser.isinstance_safe(value, self.annotation):
            return value
        if type_parser.isinstance_safe(value, DatetimeValidator.annotation):
            return value.time()
        elif type_parser.isinstance_safe(value, IntegerValidator.annotation):
            return self.int_to_time(value)
        elif type_parser.isinstance_safe(value, FloatValidator.annotation):
            return self.int_to_time(int(value))
        maybe_str = StringValidator.maybe_str(value)
        if maybe_str:
            return self.str_to_time(maybe_str)
        raise ValueError('输入应为有效时间类型')

    @classmethod
    def int_to_time(cls, value: int) -> datetime.time:
        str_value = str(value)
        length = len(str_value)
        if length == 3:
            return datetime.time(int(str_value[0]), int(str_value[1:]), 0)
        elif length == 4:
            return datetime.time(int(str_value[:2]), int(str_value[2:]), 0)
        raise ValueError('输入应为有效时间类型')

    @classmethod
    def str_to_time(cls, value: str) -> datetime.time:
        length = len(value)
        if length >= 5:
            return datetime.time.fromisoformat(value)
        raise ValueError('输入应为有效时间类型')


class TimedeltaValidator(Validator):
    """时间增量验证器"""

    name = 'timedelta'
    annotation = datetime.timedelta

    def validate(self, value, **kwargs):
        if type_parser.isinstance_safe(value, self.annotation):
            return value
        elif type_parser.isinstance_safe(value, (IntegerValidator.annotation, FloatValidator.annotation)):
            return self.annotation(seconds=value)
        maybe_str = StringValidator.maybe_str(value)
        if maybe_str:
            return self.str_to_timedelta(maybe_str)
        raise ValueError("输入应为有效时间增量类型")

    @classmethod
    def str_to_timedelta(cls, value: str):
        # Define regex patterns for both formats
        pattern_1 = re.compile(r'^(-)?(?:(\d+)d,)?(?:(\d+)d)?(\d+):(\d+):(\d+)(?:\.(\d+))?$', re.IGNORECASE)
        pattern_2 = re.compile(r'^([+-])?P?(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?$', re.IGNORECASE)

        # Try matching the first format
        match_1 = pattern_1.match(value)
        if match_1:
            sign, days_1, days_2, hours, minutes, seconds, microseconds = match_1.groups()
            days = int(days_1) if days_1 else (int(days_2) if days_2 else 0)
            hours = int(hours) if hours else 0
            minutes = int(minutes) if minutes else 0
            seconds = int(seconds) if seconds else 0
            microseconds = int(microseconds.ljust(6, '0')) if microseconds else 0

            delta = cls.annotation(days=days, hours=hours, minutes=minutes, seconds=seconds, microseconds=microseconds)
            return -delta if sign else delta

        # Try matching the second format
        match_2 = pattern_2.match(value)
        if match_2:
            sign, days, hours, minutes, seconds = match_2.groups()
            days = int(days) if days else 0
            hours = int(hours) if hours else 0
            minutes = int(minutes) if minutes else 0
            seconds = int(seconds) if seconds else 0

            delta = cls.annotation(days=days, hours=hours, minutes=minutes, seconds=seconds)
            return -delta if sign == '-' else delta
        raise ValueError('输入应为有效时间增量类型')


class DateValidator(Validator):
    """日期验证器"""

    annotation = datetime.date

    def validate(self, value, **kwargs):
        if type_parser.isinstance_safe(value, self.annotation):
            return value
        elif type_parser.isinstance_safe(value, DatetimeValidator.annotation):
            return self.datetime_to_date(value)
        try:
            if type_parser.isinstance_safe(value, (StringValidator.annotation, FloatValidator.annotation,
                                                   IntegerValidator.annotation)):
                return DatetimeValidator.str_or_int_to_datetime(value).date()
        except ValueError:
            raise ValueError("输入应为有效日期类型")
        raise ValueError("输入应为有效日期类型")

    @staticmethod
    def datetime_to_date(value: datetime.datetime) -> datetime.date:
        return value.date()


class EnumValidator(Validator):
    """枚举验证器"""

    name = 'enum'
    annotation = enum.Enum

    def __init__(self, target_enum: optional[enum.Enum] = None, use_value: bool = True):
        self.target_enum: optional[enum.Enum] = target_enum
        self.use_value = use_value
        self.names = []
        self.values = []
        self.update_validator()

    def validate(self, value, **kwargs):
        try:
            if self.target_enum is None and type_parser.issubclass_safe(value, self.annotation):
                return value
            elif self.target_enum and type_parser.isinstance_safe(value, self.target_enum):
                return value
            elif self.target_enum and type_parser.isinstance_safe(value, IntegerValidator.annotation):
                return self.int_to_enum(value)
            maybe_str = StringValidator.maybe_str(value, raise_error=False)
            if self.target_enum and maybe_str:
                return self.str_to_enum(maybe_str)
        except (Exception,):
            self.raise_error()
        self.raise_error()

    def update_validator(self):
        self.name = f'enum[{str(self.target_enum)}]' if self.target_enum is not None else 'enum'
        if self.target_enum:
            for item in self.target_enum:
                self.names.append(item.name)
                self.values.append(item.value)

    def int_to_enum(self, value: int):
        return self.target_enum(value)

    def str_to_enum(self, value: str):
        if self.use_value:
            return self.target_enum(value)
        return self.target_enum[value]

    @property
    def exact_values(self):
        return self.values if self.use_value else self.names

    @property
    def exact_text(self):
        return f'{",".join([f"`{value}`" for value in self.exact_values])}'

    def raise_error(self) -> NoReturn:
        if self.target_enum:
            raise ValueError(f'输入应为 {self.exact_text}')
        else:
            raise ValueError('输入应为枚举类型')


# TODO
class DequeValidator(Validator):
    """队列验证器"""

    name = 'deque'
    annotation = Deque
    deque: List[Validator]

    @classmethod
    def validate(cls, value: Any, check: bool = True):
        return cls.validator_type(value)


class UuidValidator(Validator):
    """UUID类型验证器"""

    name = 'uuid'
    annotation = uuid.UUID

    def __init__(self, version: optional[int] = None):
        self.version: optional[int] = version

    def validate(self, value, **kwargs) -> uuid.UUID:
        try:
            if type_parser.isinstance_safe(value, self.annotation):
                self.check_version(value, self.version)
                return value
            maybe_str = StringValidator.maybe_str(value, raise_error=False)
            if maybe_str:
                return self.str_to_uuid(maybe_str)
        except (Exception,):
            raise ValueError('输入应为有效UUID类型')
        raise ValueError('输入应为有效UUID类型')

    @staticmethod
    def check_version(value: uuid.UUID, version: optional[int]):
        if version and value.version != version:
            raise ValueError(f'UUID版本应为{version}')
        return True

    def str_to_uuid(self, value: str) -> uuid.UUID:
        res = uuid.UUID(value)
        self.check_version(res, self.version)
        return res


def matching_validator(annotation: _T):
    """匹配验证器"""
    if annotation in BASE_VALIDATORS:
        return BASE_VALIDATORS[annotation]
    elif type_parser.is_optional(annotation):
        return OptionalValidator.build(annotation)
    elif type_parser.is_union(annotation):
        return UnionValidator.build(annotation)
    elif type_parser.is_literal(annotation):
        return LiteralValidator.build(annotation)
    elif type_parser.is_tuple(annotation):
        return TupleValidator.build(annotation)
    return AnyValidator()


BASE_VALIDATORS = {
    Any: AnyValidator(),
    str: StringValidator(),
    bool: BoolValidator(),
    int: IntegerValidator(),
    float: FloatValidator(),
    bytes: BytesValidator(),
    Decimal: DecimalValidator(),
    datetime.datetime: DatetimeValidator(),
    datetime.date: DateValidator(),
    datetime.time: TimeValidator(),
    datetime.timedelta: TimedeltaValidator(),
    enum.Enum: EnumValidator(),
    uuid.UUID: UuidValidator(),
}