# -*- coding:utf-8 -*-
import datetime
import decimal
import enum
from typing import Any

from .type_parser import type_parser
from .constants import _T
from decimal import Decimal


class Validator:
    """验证器基类"""

    target_type: _T = None

    def validate(self, value, **kwargs):
        pass

    def get_name(self):
        return self.target_type


class StringValidator(Validator):
    """字符串验证器"""

    target_type = str

    def validate(self, value, allow_number: bool = True, **kwargs):
        if type_parser.isinstance_safe(value, self.target_type):
            return value
        elif type_parser.isinstance_safe(value, bytes):
            return value.decode('utf-8')
        elif type_parser.isinstance_safe(value, bytearray):
            return value.decode('utf-8')
        elif allow_number and type_parser.isinstance_safe(value, (int, float, decimal.Decimal, bool, enum.Enum)):
            return self.target_type(value)

        raise ValueError('Input should be string')

class BoolValidator(Validator):
    """布尔验证器"""

    validator_type = bool

    @classmethod
    def validate(cls, value: Any):
        return cls.validator_type(value)


class IntegerValidator(Validator):
    """整型验证器"""

    validator_type = int

    @classmethod
    def validate(cls, value: Any):
        return cls.validator_type(value)


class FloatValidator(Validator):
    """浮点验证器"""

    validator_type = float

    @classmethod
    def validate(cls, value: Any):
        return cls.validator_type(value)


class DecimalValidator(Validator):
    """Decimal验证器"""

    validator_type = Decimal

    @classmethod
    def validate(cls, value: Any):
        return cls.validator_type(value)


class BytesValidator(Validator):
    """字节验证器"""

    validator_type = bytes

    @classmethod
    def validate(cls, value: Any):
        return cls.validator_type(value)


class DatetimeValidator(Validator):
    """日期时间验证器"""

    default_format = "%Y-%m-%d %H:%M:%S"
    validator_type = datetime.datetime

    @classmethod
    def validate(cls, value: Any):
        return cls.validator_type.strptime(value, cls.default_format)


class DateValidator(Validator):
    """日期验证器"""

    default_format = "%Y-%m-%d"
    validator_type = datetime.date
    validator_type2 = datetime.datetime

    @classmethod
    def validate(cls, value: Any, check: bool = True):
        return cls.validator_type2.strptime(value, cls.default_format).date()


class EnumValidator(Validator):
    """枚举验证器"""

    validator_type = enum.Enum

    @classmethod
    def validate(cls, value: Any, check: bool = True):
        return cls.validator_type(value)


DEFAULT_VALIDATORS = {
    str: StringValidator(),
    bool: BoolValidator,
    int: IntegerValidator,
    float: FloatValidator,
    Decimal: DecimalValidator,
    bytes: BytesValidator,
    datetime.datetime: DatetimeValidator,
    datetime.date: DateValidator,
    enum.Enum: EnumValidator,
}