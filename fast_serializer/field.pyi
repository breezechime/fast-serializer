from typing import Union, Callable, Any

from fast_serializer.serializer import Serializer
from fast_serializer.types import optional, number
from fast_serializer.validator import Validator


class Field:
    """字段名"""
    name: str

    """JsonSchema标题"""
    title: optional[str]

    """注解"""
    annotation: optional[type[Any]]

    """验证器"""
    validator: optional[Validator]

    """序列化器"""
    serializer: optional[Serializer]

    """默认值"""
    default: Any

    """默认工厂"""
    default_factory: optional[Callable]

    """是否必填"""
    required: optional[bool]

    """是否初始化"""
    init: optional[bool]

    """是否显示"""
    repr: optional[bool]

    """别名"""
    alias: optional[str]

    """验证别名"""
    val_alias: optional[str]

    """序列化别名"""
    ser_alias: optional[str]

    """最小"""
    min: optional[number]

    """最大"""
    max: optional[number]

    """最短"""
    min_length: optional[int]

    """最长"""
    max_length: optional[int]

    """描述"""
    description: optional[str]

    """排除序列化"""
    exclude: optional[bool]

    """是否抛弃"""
    deprecated: optional[bool]

    """是否冻结"""
    frozen: optional[bool]

    """"""
    init_var: optional[bool]

    """验证器参数"""
    validator_kwargs: optional[Union[dict, list]]

    """序列化器参数"""
    serializer_kwargs: optional[Union[dict, list]]

    """子验证器参数"""
    sub_validator_kwargs: optional[Union[dict, list]]

    """子序列化器参数"""
    sub_serializer_kwargs: optional[Union[dict, list]]

    def __init__(self, **kwargs): ...

    def set_annotation(self, annotation): ...

    def get_default_value(self): ...


def field(
    default=None,
    *,
    default_factory=None,
    required: optional[bool] = None,
    min_length: optional[int] = None,
    max_length: optional[int] = None,
    validator_kwargs: optional[dict] = None,
    sub_validator_kwargs: optional[Union[dict, list]] = None,
    **kwargs
) -> Field: ...