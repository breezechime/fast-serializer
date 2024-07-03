# -*- coding:utf-8 -*-
import dataclasses
from typing import Literal
from .types import optional
from .globals import GlobalSetting


ExtraValues = Literal['allow', 'ignore', 'forbid']


@dataclasses.dataclass
class DataclassConfig:
    """快速数据类配置"""

    """数据类标题"""
    title: str = None

    """数据类描述"""
    description: str = None

    """键名驼峰转换到下划线。默认为“False”。"""
    camel_to_snake: bool = False

    """键名下划线转换到驼峰。默认为“False”。"""
    snake_to_camel: bool = False

    """是否为str类型去掉前导和尾部空白。"""
    str_strip_whitespace: bool = False

    """str类型的最小长度，空为不限制"""
    str_min_length: optional[int] = None

    """str类型的最大长度，空为不限制"""
    str_max_length: optional[int] = None

    """
    *`allow`-允许任何额外的属性。
    *`forbid`-禁止任何额外的属性。
    *`ignore`-忽略任何额外的属性。
    """
    extra: optional[ExtraValues] = 'ignore'

    """数据类是否是伪不可变的"""
    frozen: bool = False

    """
    数据类更改时是否验证数据。默认为“False”。
    FastDataclass的默认行为是在创建数据类时验证数据。
    如果用户在创建数据类后更改了数据，则不重新验证数据类。"""
    validate_on_change: bool = False

    """是否允许无穷大（“+inf”和“-inf”）和NaN值浮动字段。默认为“True”。"""
    allow_inf_nan: bool = True

    """datetime格式化"""
    datetime_format: str = "%Y-%m-%d %H:%M:%S"

    """date格式化"""
    date_format: str = "%Y-%m-%d"

    """默认必填"""
    required: optional[bool] = None

    eq: bool = True

    order: bool = False

    unsafe_hash: bool = False

    def __post_init__(self):
        if self.required is None:
            self.required = GlobalSetting.get_dataclass_default_required()