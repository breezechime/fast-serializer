# -*- coding:utf-8 -*-
import re
import types
from types import MappingProxyType
from typing import TypeVar

"""用于类型标注 Used for type annotation"""
_T = TypeVar('_T')


class DefaultFactory:
    """# A sentinel object for default values to signal that a default
    factory will be used.  This is given a nice repr() which will appear
    in the function signature of dataclasses constructors."""

    def __repr__(self):
        return '<factory>'


_DEFAULT_FACTORY = DefaultFactory()


# class Unset:
#     """A sentinel object to detect if a parameter is supplied or not.  Use a class to give it a better repr."""
#
#     def __repr__(self):
#         return 'UNSET'
#
#
# UNSET = Unset()

_EMPTY_METADATA: MappingProxyType = types.MappingProxyType({})


class _PseudoField:
    """Markers for the various kinds of fields and pseudo-fields. 各种字段和伪字段的标记。"""

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name


_BASE_FIELD = _PseudoField('_FIELD')
_FIELD_CLASS_VAR = _PseudoField('_FIELD_CLASS_VAR')
_FIELD_INIT_VAR = _PseudoField('_FIELD_INIT_VAR')


# The name of an attribute on the class where we store the Field
# objects.  Also used to check if a class is a Data Class.
_DATACLASS_FIELDS_NAME = 'dataclass_fields'


# The name of an attribute on the class that stores the config to
# @dataclass.
_DATACLASS_CONFIG_NAME = 'dataclass_config'

_FAST_SERIALIZER_NAME = '__fast_serializer__'

_VALIDATOR_KWARGS_NAME = 'validator_kwargs'

_SUB_VALIDATOR_KWARGS_NAME = 'sub_validator_kwargs'

_SERIALIZER_KWARGS_NAME = 'serializer_kwargs'

# 数据类装饰器名
_FAST_DATACLASS_DECORATORS_NAME = '__fast_dataclass_decorators__'

# The name of the function, that if it exists, is called at the end of
# __init__.
_POST_INIT_NAME = '__post_init__'


# String regex that string annotations for ClassVar or InitVar must match.
# https://bugs.python.org/issue33453 for details.
_MODULE_IDENTIFIER_RE = re.compile(r'^(?:\s*(\w+)\s*\.)?\s*(\w+)')


class _InitVarMeta(type):

    def __getitem__(self, params):
        return self


class InitVar(metaclass=_InitVarMeta):
    pass