# -*- coding:utf-8 -*-
from sqlalchemy import Column, String, Integer, BigInteger, DECIMAL, Enum, JSON, Boolean, Date, DateTime
from ..types import optional


class ModelField(Column):
    """模型字段"""
    pass


class IntegerField(ModelField):
    """整数型字段 int"""

    def __init__(self, *args, **kwargs):
        super().__init__(Integer, *args, **kwargs)


class BigIntegerField(ModelField):
    """长整型字段 bigint"""

    def __init__(self, *args, **kwargs):
        super().__init__(BigInteger, *args, **kwargs)


class CharField(ModelField):
    """字符字段"""

    def __init__(self, *args, length: optional[int] = 255, **kwargs):
        super().__init__(String(length), *args, **kwargs)


class FloatField(ModelField):
    """浮点型字段 float"""

    def __init__(self, *args, precision: str = '10,2', **kwargs):
        """FloatField(precision='10,2') || 2.0版本后sqlalchemy更新了"""
        super().__init__(Float(precision=precision), *args, **kwargs)  # type: ignore


class DecimalField(ModelField):
    """高精度型字段"""

    def __init__(self, *args, precision: int = 10, scale: int = 2, **kwargs):
        super().__init__(DECIMAL(precision=precision, scale=scale), *args, **kwargs)


class BooleanField(ModelField):
    """布尔型字段 bool"""

    def __init__(self, *args, **kwargs):
        super().__init__(Boolean, *args, **kwargs)


class DateField(ModelField):
    """日期型字段 date"""

    def __init__(self, *args, **kwargs):
        super().__init__(Date, *args, **kwargs)


class DateTimeField(ModelField):
    """日期时间型字段 datetime"""

    def __init__(self, *args, **kwargs):
        super().__init__(DateTime, *args, **kwargs)


class EnumField(ModelField):
    """枚举型字段 enum"""

    def __init__(self, *args, value: Enum, **kwargs):
        super().__init__(Enum(value), *args, **kwargs)


class JSONField(ModelField):
    """JSON字段"""

    def __init__(self, *args, **kwargs):
        super().__init__(JSON, *args, **kwargs)