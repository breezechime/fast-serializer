# -*- coding:utf-8 -*-
from types import MappingProxyType
from typing import Optional

from .constants import _EMPTY_METADATA, _DEFAULT_FACTORY
from .utils import _recursive_repr, _format_type
from dataclasses import MISSING


class Field(object):
    """字段"""

    __slots__ = ('name', 'type', 'default', 'default_factory', 'required', 'init', 'repr', 'hash', 'compare', 'metadata', 'description',
                 '_field_type')

    def __init__(self, default=None, default_factory=None, required=False, init=True, repr=True, hash=True, compare=True, metadata=None,
                 description=None):
        if default is MISSING:
            default = None
        if default_factory is MISSING:
            default_factory = None

        if default is not None and default_factory is not None:
            raise ValueError(f'不能同时指定 default 和 default_factory'
                             f'\n\tcannot specify both default and default_factory')

        self.name = None
        self.type = None
        self.default = default
        self.default_factory = default_factory
        self.required = required
        self.init = init
        self.repr = repr
        self.hash = hash
        self.compare = compare
        self.metadata = _EMPTY_METADATA if metadata is None else MappingProxyType(metadata)
        self.description = description

    def set_type(self, _type):
        if _type is Optional:
            raise RuntimeError("Optional 必须添加内部类型")
        self.type = _type

    @_recursive_repr
    def __repr__(self):
        return (f"Field(name={self.name!r}, "
                f"type={_format_type(self.type)}, "
                f"default={self.default!r}, "
                f"default_factory={self.default_factory!r}, "
                f"required={self.required!r}, "
                f"init={self.init!r}, "
                f"repr={self.repr!r}, "
                f"hash={self.hash!r}, "
                f"compare={self.compare}, "
                f"metadata={self.metadata!r}, "
                f"description={self.description!r})")


# This function is used instead of exposing Field creation directly,
# so that a type checker can be told (via overloads) that this is a
# function whose type depends on its parameters.
def field(*, default=None, default_factory=None, required=False, **kwargs) -> Field:
    """Return an object to identify dataclass fields.

    default is the default value of the field.  default_factory is a
    0-argument function called to initialize a field's value.  If init
    is True, the field will be a parameter to the class's __init__()
    function.  If repr is True, the field will be included in the
    object's repr().  If hash is True, the field will be included in
    the object's hash().  If compare is True, the field will be used
    in comparison functions.  metadata, if specified, must be a
    mapping which is stored but not otherwise examined by dataclass.

    It is an error to specify both default and default_factory.
    """
    return Field(default=default, default_factory=default_factory, required=required, **kwargs)