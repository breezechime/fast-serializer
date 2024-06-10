# -*- coding:utf-8 -*-
import datetime
import enum
import uuid
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any, Deque, Generator
from .constants import _T
from .type_parser import type_parser
from .types import optional
from .utils import _format_type


class Validator(ABC):
    """验证器基类"""

    name: str
    target_type: _T

    @abstractmethod
    def validate(self, value, **kwargs):
        """验证数据并返回正确数据或抛出异常"""
        pass

    def is_instance(self, value, target_type=None) -> bool:
        target_type = target_type or self.target_type
        return type_parser.isinstance_safe(value, target_type)

    def get_name(self) -> str:
        return self.name

    def __repr__(self):
        return f"{self.__class__.__name__}(\n\tname: {self.name},\n\ttarget_type: {self.target_type}\n)"


class AnyValidator(Validator):
    """任意类型验证器"""

    name = 'any'
    target_type = Any

    def validate(self, value, **kwargs):
        return value


class StringValidator(Validator):
    """字符串验证器"""

    name = 'str'
    target_type = str

    def validate(self, value, allow_number: bool = True, **kwargs) -> str:
        maybe_str = self.maybe_str(value)
        if maybe_str:
            return maybe_str
        elif type_parser.isinstance_safe(value, bytearray):
            return value.decode('utf-8')
        numbers_types = (IntegerValidator.target_type, FloatValidator.target_type,
                         DecimalValidator.target_type, BoolValidator.target_type)
        if allow_number and type_parser.isinstance_safe(value, numbers_types):
            return self.target_type(value)

        raise ValueError('Input should be string')

    @classmethod
    def maybe_str(cls, value, raise_error: bool = True) -> optional[str]:
        if type_parser.isinstance_safe(value, cls.target_type):
            return value
        elif type_parser.isinstance_safe(value, BytesValidator.target_type):
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
    target_type = bool

    def validate(self, value, **kwargs) -> bool:
        if type_parser.isinstance_safe(value, self.target_type):
            return value
        elif type_parser.isinstance_safe(value, IntegerValidator.target_type):
            return self.int_to_bool(value)
        elif type_parser.isinstance_safe(value, FloatValidator.target_type):
            return self.int_to_bool(IntegerValidator.target_type(value))
        elif type_parser.isinstance_safe(value, StringValidator.target_type):
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
    target_type = int

    def validate(self, value, **kwargs):
        if type_parser.isinstance_safe(value, self.target_type):
            return value
        elif type_parser.isinstance_safe(value, BoolValidator.target_type):
            return self.bool_to_int(value)
        elif type_parser.isinstance_safe(value, FloatValidator.target_type):
            return self.float_to_int(value)
        elif type_parser.isinstance_safe(value, DecimalValidator.target_type):
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
    target_type = float

    def validate(self, value, **kwargs):
        if type_parser.isinstance_safe(value, self.target_type):
            return value
        elif type_parser.isinstance_safe(value, IntegerValidator.target_type):
            return self.target_type(value)
        elif type_parser.isinstance_safe(value, DecimalValidator.target_type):
            return self.target_type(value)
        maybe_str = StringValidator.maybe_str(value)
        if maybe_str:
            return self.target_type(value)

        raise ValueError('Input should be float')


class DecimalValidator(FloatValidator):
    """Decimal验证器"""

    name = 'decimal'
    target_type = Decimal

    def validate(self, value, **kwargs):
        if self.is_instance(value, self.target_type):
            return value
        elif type_parser.isinstance_safe(value, IntegerValidator.target_type):
            return self.target_type(value)
        elif type_parser.isinstance_safe(value, FloatValidator.target_type):
            return self.target_type(value)
        maybe_str = StringValidator.maybe_str(value)
        if maybe_str:
            return self.target_type(value)

        raise ValueError('Input should be decimal')


class BytesValidator(Validator):
    """字节验证器"""

    name = 'bytes'
    target_type = bytes

    def validate(self, value, **kwargs):
        if type_parser.isinstance_safe(value, self.target_type):
            return value
        elif type_parser.isinstance_safe(value, StringValidator.target_type):
            return value.encode('utf-8')
        elif type_parser.isinstance_safe(value, bytearray):
            return self.target_type(value)


class TargetTypeValidator(Validator):
    """目标类型验证器"""

    name = 'target_type'

    def __init__(self, target_type: _T):
        self.target_type = target_type
        self.name = _format_type(target_type)

    def validate(self, value, **kwargs):
        if type_parser.isinstance_safe(value, self.target_type):
            return value
        raise ValueError(f'Input should be {self.name}')


# TODO
class UnionValidator(Validator):
    """联合类型验证器"""

    name = 'union'

    def __init__(self, validators=None):
        self.validators = validators or []

    def validate(self, value, **kwargs):
        pass


# TODO
class LiteralValidator(Validator):
    """字面量类型验证器"""

    name = 'literal'

    def validate(self, value, **kwargs):
        pass


# TODO
class FastDataclassValidator(Validator):
    """快速数据类验证器"""

    def validate(self, value, **kwargs):
        pass


# TODO
class PydanticModelValidator(Validator):
    """Pydantic模型验证器"""

    def validate(self, value, **kwargs):
        pass


# TODO
class SqlalchemyModelValidator(Validator):
    """Sqlalchemy模型验证器"""

    def validate(self, value, **kwargs):
        pass


# TODO
class DataclassValidator(Validator):
    """数据类验证器"""

    def validate(self, value, **kwargs):
        pass


# TODO
class DictValidator(Validator):
    """字典验证器"""

    def validate(self, value, **kwargs):
        pass


# TODO
class TypedDictValidator(Validator):
    """带类型字典验证器"""

    def validate(self, value, **kwargs):
        pass


# TODO
class ListValidator(Validator):
    """列表验证器"""

    def validate(self, value, **kwargs):
        pass


# TODO
class TupleValidator(Validator):
    """元组验证器"""

    def validate(self, value, **kwargs):
        pass


# TODO
class SetValidator(Validator):
    """集合验证器"""

    def validate(self, value, **kwargs):
        pass


# TODO
class FrozenValidator(Validator):
    """冻结集合验证器"""

    name = 'frozenset'
    target_type = frozenset

    def validate(self, value, **kwargs):
        pass


# TODO
class GeneratorValidator(Validator):
    """生成器验证器"""

    name = 'generator'
    target_type = Generator

    def validate(self, value, **kwargs):
        pass


# TODO
class CallValidator(Validator):

    def validate(self, value, **kwargs):
        pass


# TODO
class CallableValidator(Validator):

    def validate(self, value, **kwargs):
        pass


# TODO
class DatetimeValidator(Validator):
    """日期时间验证器"""

    name = 'datetime'
    target_type = datetime.datetime

    def validate(self, value, **kwargs):
        return self.target_type(value)


# TODO
class TimeValidator(Validator):
    """时间验证器"""

    name = 'time'
    target_type = datetime.time

    def validate(self, value, **kwargs):
        return self.target_type(value)


# TODO
class TimedeltaValidator(Validator):
    """时间间隔验证器"""

    name = 'timedelta'
    target_type = datetime.timedelta

    def validate(self, value, **kwargs):
        return self.target_type(value)


# TODO
class DateValidator(Validator):
    """日期验证器"""

    default_format = "%Y-%m-%d"
    validator_type = datetime.date
    validator_type2 = datetime.datetime

    @classmethod
    def validate(cls, value: Any, check: bool = True):
        return cls.validator_type2.strptime(value, cls.default_format).date()


# TODO
class EnumValidator(Validator):
    """枚举验证器"""

    validator_type = enum.Enum

    @classmethod
    def validate(cls, value: Any, check: bool = True):
        return cls.validator_type(value)


# TODO
class DequeValidator(Validator):
    """队列验证器"""

    name = 'deque'
    validator_type = Deque

    @classmethod
    def validate(cls, value: Any, check: bool = True):
        return cls.validator_type(value)


class UuidValidator(Validator):
    """UUID类型验证器"""

    name = 'uuid'
    target_type = uuid.UUID

    def __init__(self, version: optional[int] = None):
        self.version: optional[int] = version

    def validate(self, value, **kwargs) -> uuid.UUID:
        if type_parser.isinstance_safe(value, self.target_type):
            self.check_version(value, self.version)
            return value
        maybe_str = StringValidator.maybe_str(value, raise_error=False)
        if maybe_str:
            return self.str_to_uuid(maybe_str)
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


# TODO
class UrlValidator(Validator):
    """链接验证器"""

    name = 'url'

    def validate(self, value, **kwargs):
        pass


# TODO
class EmailValidator(Validator):
    """邮箱验证器"""

    name = 'email'

    def validate(self, value, **kwargs):
        pass


DEFAULT_VALIDATORS = {
    str: StringValidator(),
    bool: BoolValidator(),
    int: IntegerValidator(),
    float: FloatValidator(),
    Decimal: DecimalValidator(),
    bytes: BytesValidator(),
    datetime.datetime: DatetimeValidator(),
    datetime.date: DateValidator(),
    enum.Enum: EnumValidator(),
}