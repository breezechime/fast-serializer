# -*- coding:utf-8 -*-
import collections
from types import FunctionType
from typing import (
    Optional,
    Union,
    Literal,
    ClassVar,
    Dict,
    List,
    Mapping,
    Collection,
    Any,
    NoReturn,
    Final,
    Tuple,
    Sequence,
    Counter,
    get_origin, Iterable, Set,
)
from .constants import _DATACLASS_FIELDS_NAME
from .utils import isinstance_safe, issubclass_safe


class TypeParser:
    """类型解析器"""

    """必须有子类型的类型"""
    __required_subtype_types__: ClassVar[list] = [Optional, Union, ClassVar]

    """希望有子类型的类型"""
    __hope_subtype_types__: ClassVar[list] = [Dict, List, Mapping, Collection, Tuple, Sequence, Counter]

    def is_any(self, value: Any) -> bool:
        """是否任意类型的"""
        if value is None:
            return False
        return value is Any

    def is_optional(self, annotation) -> bool:
        """是否可为空"""
        if annotation is None:
            return False
        return annotation is Optional or getattr(annotation, '_name', None) == 'Optional' or annotation is Any

    def is_no_return(self, annotation) -> bool:
        """是否为不返回类型"""
        if annotation is None:
            return False
        return annotation is NoReturn

    def is_union(self, annotation) -> bool:
        """是否联合类型的"""
        if annotation is None:
            return False
        return get_origin(annotation) is Union or getattr(get_origin(annotation), '_name', None) == 'Union'

    def is_literal(self, annotation) -> bool:
        """是否字面量类型的"""
        if annotation is None:
            return False
        origin = get_origin(annotation)
        return origin is Literal or getattr(origin, '_name', None) == 'Literal'

    def is_final(self, value) -> bool:
        """是否最后类型的"""
        if value is None:
            return False
        return value is Final or getattr(get_origin(value), '_name', None) == 'Final'

    def is_class_var(self, value) -> bool:
        """是否为类共享类型的"""
        if value is None:
            return False
        return value is ClassVar or getattr(get_origin(value), '_name', None) == 'ClassVar'

    def is_collection(self, value) -> bool:
        """是否集合类型的"""
        if value is None:
            return False
        return issubclass_safe(get_origin(value), Collection)

    def is_deque(self, value) -> bool:
        """是否双端队列类型的"""
        if value is None:
            return False
        return isinstance_safe(value, collections.deque)

    def is_iterable(self, value) -> bool:
        """是否可迭代类型的"""
        if value is None:
            return False
        return value is Iterable or issubclass_safe(get_origin(value), Iterable)

    def is_list(self, value) -> bool:
        """是否列表类型的"""
        if value is None:
            return False
        return isinstance_safe(value, list) or issubclass_safe(get_origin(value), List)

    def is_tuple(self, value) -> bool:
        """是否元组类型的"""
        if value is None:
            return False
        return isinstance_safe(value, tuple) or issubclass_safe(get_origin(value), Tuple)

    def is_set(self, value) -> bool:
        """是否集合类型的"""
        if value is None:
            return False
        return isinstance_safe(value, set) or issubclass_safe(get_origin(value), Set)

    def is_mapping(self, value) -> bool:
        """是否映射类型的"""
        if value is None:
            return False
        return issubclass_safe(get_origin(value), Mapping)

    def is_dict(self, value) -> bool:
        """是否字典类型的"""
        if value is None:
            return False
        return value is Dict or isinstance_safe(value, dict) or issubclass_safe(get_origin(value), Dict)

    def is_sequence(self, value) -> bool:
        """是否序列类型的"""
        if value is None:
            return False
        return issubclass_safe(get_origin(value), Sequence)

    def is_counter(self, value) -> bool:
        """是否计数器类型的"""
        if value is None:
            return False
        return issubclass_safe(get_origin(value), Counter)

    def is_function(self, value) -> bool:
        """是否为函数"""
        return isinstance_safe(value, FunctionType)

    def is_fast_dataclass(obj):
        cls = obj if isinstance(obj, type) else type(obj)
        return hasattr(cls, _DATACLASS_FIELDS_NAME)

    def is_pydantic_model(self, value) -> bool:
        """是否为pydantic模型"""
        return hasattr(value, 'model_fields') and hasattr(value, '__pydantic_validator__')

    def get_origin_safe(self, v):
        return get_origin(v)

    def repair_type(self, value):
        """检查类型是否合法，并修正"""
        if value in self.__required_subtype_types__:
            raise RuntimeError(f"{value} 必须包含子类型")
        elif value in self.__hope_subtype_types__:
            return get_origin(self.__hope_subtype_types__[self.__hope_subtype_types__.index(value)])
        return value


"""类型解析器实例（减少类开支）"""
type_parser = TypeParser()