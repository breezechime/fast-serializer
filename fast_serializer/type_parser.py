# -*- coding:utf-8 -*-
from typing import (
    Optional,
    Union,
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
    get_origin,
)


class TypeParser:
    """类型解析器"""

    """必须有子类型的类型"""
    __required_subtype_types__: ClassVar[list] = [Optional, Union, ClassVar]

    """希望有子类型的类型"""
    __hope_subtype_types__: ClassVar[list] = [Dict, List, Mapping, Collection]

    @classmethod
    def is_any(cls, value: Any) -> bool:
        """是否任意类型的"""
        if value is None:
            return False

        return value is Any

    @classmethod
    def is_optional(cls, value) -> bool:
        """是否可为空"""
        if value is None:
            return False

        return value is Optional or getattr(value, '_name', None) == 'Optional' or value is Any

    @classmethod
    def is_no_return(cls, value) -> bool:
        """是否为不返回类型"""
        if value is None:
            return False

        return value is NoReturn

    @classmethod
    def is_union(cls, value) -> bool:
        """是否联合类型的"""
        if value is None:
            return False

        return get_origin(value) is Union or getattr(get_origin(value), '_name', None) == 'Union'

    @classmethod
    def is_final(cls, value) -> bool:
        """是否最后类型的"""
        if value is None:
            return False

        return value is Final or getattr(get_origin(value), '_name', None) == 'Final'

    @classmethod
    def is_class_var(cls, value) -> bool:
        """是否为类共享类型的"""
        if value is None:
            return False

        return value is ClassVar or getattr(get_origin(value), '_name', None) == 'ClassVar'

    @classmethod
    def is_collection(cls, value) -> bool:
        """是否集合类型的"""
        if value is None:
            return False

        return cls.issubclass_safe(get_origin(value), Collection)

    @classmethod
    def is_list(cls, value) -> bool:
        """是否列表类型的"""
        if value is None:
            return False

        return cls.issubclass_safe(get_origin(value), List)

    @classmethod
    def is_tuple(cls, value) -> bool:
        """是否元组类型的"""
        if value is None:
            return False

        return cls.issubclass_safe(get_origin(value), Tuple)

    @classmethod
    def is_mapping(cls, value) -> bool:
        """是否映射类型的"""
        if value is None:
            return False

        return cls.issubclass_safe(get_origin(value), Mapping)

    @classmethod
    def is_dict(cls, value) -> bool:
        """是否字典类型的"""
        if value is None:
            return False

        return cls.issubclass_safe(get_origin(value), Dict)

    @classmethod
    def is_sequence(cls, value) -> bool:
        """是否序列类型的"""
        if value is None:
            return False

        return cls.issubclass_safe(get_origin(value), Sequence)

    @classmethod
    def is_counter(cls, value) -> bool:
        """是否计数器类型的"""
        if value is None:
            return False

        return cls.issubclass_safe(get_origin(value), Counter)

    @classmethod
    def issubclass_safe(cls, value, check_type):
        try:
            return issubclass(value, check_type)
        except (Exception,):
            return False

    def repair_type(self, value):
        """检查类型是否合法，并修正"""
        if value in self.__required_subtype_types__:
            raise RuntimeError(f"{value} 必须包含子类型")
        elif value in self.__hope_subtype_types__:
            return get_origin(self.__hope_subtype_types__[self.__hope_subtype_types__.index(value)])
        return value
