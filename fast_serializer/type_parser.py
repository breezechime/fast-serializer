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
    __hope_subtype_types__: ClassVar[list] = [Dict, List, Mapping, Collection, Tuple, Sequence, Counter]

    def is_any(self, value: Any) -> bool:
        """是否任意类型的"""
        if value is None:
            return False
        return value is Any

    def is_optional(self, value) -> bool:
        """是否可为空"""
        if value is None:
            return False
        return value is Optional or getattr(value, '_name', None) == 'Optional' or value is Any

    def is_no_return(self, value) -> bool:
        """是否为不返回类型"""
        if value is None:
            return False
        return value is NoReturn

    def is_union(self, value) -> bool:
        """是否联合类型的"""
        if value is None:
            return False
        return get_origin(value) is Union or getattr(get_origin(value), '_name', None) == 'Union'

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
        return self.issubclass_safe(get_origin(value), Collection)

    def is_list(self, value) -> bool:
        """是否列表类型的"""
        if value is None:
            return False
        return self.issubclass_safe(get_origin(value), List)

    def is_tuple(self, value) -> bool:
        """是否元组类型的"""
        if value is None:
            return False
        return self.issubclass_safe(get_origin(value), Tuple)

    def is_mapping(self, value) -> bool:
        """是否映射类型的"""
        if value is None:
            return False
        return self.issubclass_safe(get_origin(value), Mapping)

    def is_dict(self, value) -> bool:
        """是否字典类型的"""
        if value is None:
            return False
        return self.issubclass_safe(get_origin(value), Dict)

    def is_sequence(self, value) -> bool:
        """是否序列类型的"""
        if value is None:
            return False

        return self.issubclass_safe(get_origin(value), Sequence)

    def is_counter(self, value) -> bool:
        """是否计数器类型的"""
        if value is None:
            return False

        return self.issubclass_safe(get_origin(value), Counter)

    def issubclass_safe(self, value, target_type):
        try:
            return issubclass(value, target_type)
        except (Exception,):
            return False

    def isinstance_safe(self, value, target_type):
        try:
            return isinstance(value, target_type)
        except (Exception,):
            return False

    def repair_type(self, value):
        """检查类型是否合法，并修正"""
        if value in self.__required_subtype_types__:
            raise RuntimeError(f"{value} 必须包含子类型")
        elif value in self.__hope_subtype_types__:
            return get_origin(self.__hope_subtype_types__[self.__hope_subtype_types__.index(value)])
        return value


"""类型解析器实例（减少类开支）"""
type_parser = TypeParser()