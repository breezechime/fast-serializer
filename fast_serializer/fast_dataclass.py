# -*- coding:utf-8 -*-
import _thread
import builtins
import functools
import sys
from dataclasses import Field as DataclassField
from types import MemberDescriptorType, GenericAlias, FunctionType
from typing import ClassVar, Dict, Type, Any, List

from .constants import (_T, _DATACLASS_CONFIG_NAME, _DATACLASS_FIELDS_NAME, _BASE_FIELD,
                        _MODULE_IDENTIFIER_RE, InitVar, _FIELD_CLASS_VAR, _FIELD_INIT_VAR,
                        _FAST_DATACLASS_DECORATORS_NAME,
                        _FAST_SERIALIZER_NAME, _SUB_VALIDATOR_KWARGS_NAME)
from .dataclass_config import DataclassConfig
from .decorators import FastDataclassDecoratorInfo
from .field import Field
from .serializer import FastSerializer
from .validator import matching_validator


def _tuple_str(obj_name, fields: List[Field]):
    # Return a string representing each field of obj_name as a tuple
    # member.  So, if fields is ['x', 'y'] and obj_name is "self",
    # return "(self.x,self.y)".

    # Special case for the 0-tuple.
    if not fields:
        return '()'
    # Note the trailing comma, needed if this turns out to be a 1-tuple.
    return f'({",".join([f"{obj_name}.{f.name}" for f in fields])},)'


# This function's logic is copied from "recursive_repr" function in
# repr lib module to avoid dependency.
def _recursive_repr(user_function):
    """Decorator to make a repr function return "..." for a recursive call."""
    repr_running = set()

    @functools.wraps(user_function)
    def wrapper(self):
        key = id(self), _thread.get_ident()
        if key in repr_running:
            return '...'
        repr_running.add(key)
        try:
            result = user_function(self)
        finally:
            repr_running.discard(key)
        return result

    return wrapper


def _create_fn(name, args, body, *, _globals=None, _locals=None, return_type=None):
    # Note that we mutate locals when exec() is called.  Caller
    # beware!  The only callers are internal to this module, so no
    # worries about external callers.
    if _locals is None:
        _locals = {}
    if 'BUILTINS' not in _locals:
        _locals['BUILTINS'] = builtins
    return_annotation = ''
    if return_type is not None:
        _locals['_return_type'] = return_type
        return_annotation = '->_return_type'
    args = ','.join(args)
    body = '\n'.join(f'  {b}' for b in body)

    # Compute the text of the entire function.
    txt = f' def {name}({args}){return_annotation}:\n{body}'

    local_vars = ', '.join(_locals.keys())
    txt = f"def __create_fn__({local_vars}):\n{txt}\n return {name}"

    ns = {}
    exec(txt, _globals, ns)
    return ns['__create_fn__'](**_locals)


def _field_assign(frozen, name, value, self_name):
    # If we're a frozen class, then assign to our fields in __init__
    # via object.__setattr__.  Otherwise, just use a simple
    # assignment.
    #
    # self_name is what "self" is called in this function: don't
    # hard-code "self", since that might be a field name.
    if frozen:
        return f'BUILTINS.object.__setattr__({self_name},{name!r},{value})'
    return f'{self_name}.{name}={value}'


def _repr_fn(fields, _globals):
    fn = _create_fn('__repr__',
                    ('self',),
                    ['return self.__class__.__qualname__ + f"(' +
                     ', '.join([f"{f.name}={{self.{f.name}!r}}"
                                for f in fields]) +
                     ')"'],
                    _globals=_globals)
    return _recursive_repr(fn)


def _hash_fn(fields, _globals):
    self_tuple = _tuple_str('self', fields)
    return _create_fn('__hash__',
                      ('self',),
                      [f'return hash({self_tuple})'],
                      _globals=_globals)


def _is_class_var(field_type: Any):
    # This test uses a typing internal class, but it's the best way to
    # test if this is a ClassVar.
    return field_type is ClassVar or (type(field_type) is GenericAlias and field_type.__origin__ is ClassVar)


def _is_init_var(field_type: Any):
    # The module we're checking against is the module we're
    # currently in (dataclasses_plus.py).
    return field_type is InitVar


def _is_type(annotation, cls, a_module, a_type, is_type_predicate):
    # Given a type annotation string, does it refer to a_type in
    # a_module?  For example, when checking that annotation denotes a
    # ClassVar, then a_module is typing, and a_type is
    # typing.ClassVar.

    # It's possible to look up a_module given a_type, but it involves
    # looking in sys.modules (again!), and seems like a waste since
    # the caller already knows a_module.

    # - annotation is a string type annotation
    # - cls is the class that this annotation was found in
    # - a_module is the module we want to match
    # - a_type is the type in that module we want to match
    # - is_type_predicate is a function called with (obj, a_module)
    #   that determines if obj is of the desired type.

    # Since this test does not do a local namespace lookup (and
    # instead only a module (global) lookup), there are some things it
    # gets wrong.

    # With string annotations, cv0 will be detected as a ClassVar:
    #   CV = ClassVar
    #   @dataclass
    #   class C0:
    #     cv0: CV

    # But in this example cv1 will not be detected as a ClassVar:
    #   @dataclass
    #   class C1:
    #     CV = ClassVar
    #     cv1: CV

    # In C1, the code in this function (_is_type) will look up "CV" in
    # the module and not find it, so it will not consider cv1 as a
    # ClassVar.  This is a fairly obscure corner case, and the best
    # way to fix it would be to eval() the string "CV" with the
    # correct global and local namespaces.  However, that would involve
    # a eval() penalty for every single field of every dataclass
    # that's defined.  It was judged not worth it.

    match = _MODULE_IDENTIFIER_RE.match(annotation)
    if match:
        ns = None
        module_name = match.group(1)
        if not module_name:
            # No module name, assume the class's module did
            # "from dataclasses import InitVar".
            ns = sys.modules.get(cls.__module__).__dict__
        else:
            # Look up module_name in the class's module.
            module = sys.modules.get(cls.__module__)
            if module and module.__dict__.get(module_name) is a_module:
                ns = sys.modules.get(a_type.__module__).__dict__
        if ns and is_type_predicate(ns.get(match.group(2)), a_module):
            return True
    return False


def _generate_field(cls, field_name: str, annotation: type, dataclass_config: DataclassConfig) -> Field:
    # Return a Field object for this field name and type.  ClassVars
    # and InitVars are also returned, but marked as such (see f._field_type).
    # 返回此字段名称和类型的Field对象。ClassVars和InitVars也会返回，但标记为这样（请参阅f.field_type）。

    # If the default value isn't derived from Field, then it's only a
    # normal default value.  Convert it to a Field().
    # 如果默认值不是从Field派生的，则它只是一个普通的默认值。将其转换为Field()。

    field_or_default = getattr(cls, field_name, None)
    if isinstance(field_or_default, Field):
        """已是Field对象"""
        field = field_or_default
    elif isinstance(field_or_default, DataclassField):
        """原始数据类字段"""
        field = Field(default=field_or_default.default, default_factory=field_or_default.default_factory,
                      init=field_or_default.init, repr=field_or_default.repr)
    else:
        if isinstance(field_or_default, MemberDescriptorType):
            # This is a field in __slots__, so it has no default value.
            # 这是__slots__中的字段，因此它没有默认值。
            field_or_default = None
        field = Field(default=field_or_default)
        setattr(cls, field_name, field)  # 保留Field在未实例的数据类上

    field.name = field_name
    field.required = dataclass_config.required
    field.frozen = dataclass_config.frozen
    field.set_annotation(annotation)

    # 组装验证器参数传递
    field.validator_kwargs = field.validator_kwargs or dict()
    if field.min_length:
        field.validator_kwargs['min_length'] = field.min_length
    if field.max_length:
        field.validator_kwargs['max_length'] = field.max_length
    if field.sub_validator_kwargs:
        field.validator_kwargs[_SUB_VALIDATOR_KWARGS_NAME] = field.sub_validator_kwargs
    # 查找对应类型的验证器
    field.validator = matching_validator(annotation, **field.validator_kwargs)

    # 接下来是对InitVar和ClassVar的支持
    # Assume it's a normal field until proven otherwise.  We're next
    # going to decide if it's a ClassVar or InitVar, everything else
    # is just a normal field.
    # 在证明之前，假设它是一个普通字段。接下来，我们将决定它是ClassVar还是InitVar，其他所有内容都只是普通字段。
    setattr(field, '_field_type', _BASE_FIELD)

    # In addition to checking for actual types here, also check for
    # string annotations.  get_type_hints() won't always work for us
    # (see https://github.com/python/typing/issues/508 for example),
    # plus it's expensive and would require an eval for every string
    # annotation.  So, make the best effort to see if this is a ClassVar
    # or InitVar using regex's and checking that the thing referenced
    # is actually of the correct type.

    # For the complete discussion, see https://bugs.python.org/issue33453

    # If typing has not been imported, then it's impossible for any
    # annotation to be a ClassVar.  So, only look for ClassVar if
    # typing has been imported by any module (not necessarily cls module).
    _typing = sys.modules.get('typing')
    if _typing:
        end_if = isinstance(field.annotation, str) and _is_type(field.annotation, cls, _typing, ClassVar, _is_class_var)
        if _is_class_var(annotation) or end_if:
            annotation._field_type = _FIELD_CLASS_VAR

    # If the type is InitVar, or if it's a matching string annotation, then it's an InitVar.
    field_type = getattr(annotation, '_field_type', _BASE_FIELD)
    if field_type is _BASE_FIELD:
        # The module we're checking against is the module we're currently in (dataclasses_plus.py).
        module = sys.modules[__name__]
        if (_is_init_var(field.annotation) or (isinstance(field.annotation, str)
                                               and _is_type(field.annotation, cls, module, InitVar, _is_init_var))):
            setattr(field, '_field_type', _FIELD_INIT_VAR)

    # Validations for individual fields.  This is delayed until now,
    # instead of in the Field() constructor, since only here do we
    # know the field name, which allows for better error reporting.

    # Special restrictions for ClassVar and InitVar.
    if field_type in (_FIELD_CLASS_VAR, _FIELD_INIT_VAR):
        if field.default_factory is not None:
            raise TypeError(f'field {field.name} cannot have a default factory')
        # Should I check for other field settings? default_factory
        # seems the most serious to check for.  Maybe add others.  For
        # example, how about init=False (or really,
        # init=<not-the-default-init-value>)?  It makes no sense for
        # ClassVar and InitVar to specify init=<anything>.

    # For real fields, disallow mutable defaults for known types.
    if field_type is _BASE_FIELD and isinstance(field.default, (list, dict, set)):
        raise ValueError(f'mutable default {type(field.default)} for field {field.name} is not allowed: use default_factory')

    return field


def _set_new_attribute(cls, name, value):
    # Never overwrites an existing attribute.  Returns True if the
    # attribute already exists.
    if name in cls.__dict__:
        return True
    setattr(cls, name, value)
    return False


# Decide if/how we're going to create a hash function.  Key is
# (unsafe_hash, eq, frozen, does-hash-exist).  Value is the action to
# take.  The common case is to do nothing, so instead of providing a
# function that is a no-op, use None to signify that.
def _hash_set_none(_, __, _globals):
    return None


def _hash_add(cls, fields, _globals):
    fields = [f for f in fields if (f.compare if f.hash is None else f.hash)]
    return _set_qualname(cls, _hash_fn(fields, _globals))


def _hash_exception(cls, _, _globals):
    # Raise an exception.
    raise TypeError(f'Cannot overwrite attribute __hash__ in class {cls.__name__}')


#
#                +-------------------------------------- unsafe_hash?
#                |      +------------------------------- eq?
#                |      |      +------------------------ frozen?
#                |      |      |      +----------------  has-explicit-hash?
#                |      |      |      |
#                |      |      |      |        +-------  action
#                |      |      |      |        |
#                v      v      v      v        v
_hash_action = {(False, False, False, False): None,
                (False, False, False, True): None,
                (False, False, True, False): None,
                (False, False, True, True): None,
                (False, True, False, False): _hash_set_none,
                (False, True, False, True): None,
                (False, True, True, False): _hash_add,
                (False, True, True, True): None,
                (True, False, False, False): _hash_add,
                (True, False, False, True): _hash_exception,
                (True, False, True, False): _hash_add,
                (True, False, True, True): _hash_exception,
                (True, True, False, False): _hash_add,
                (True, True, False, True): _hash_exception,
                (True, True, True, False): _hash_add,
                (True, True, True, True): _hash_exception,
                }


# See https://bugs.python.org/issue32929#msg312829 for an if-statement
# version of this table.


def _set_qualname(cls, value):
    # Ensure that the functions returned from _create_fn uses the proper
    # __qualname__ (the class they belong to).
    if isinstance(value, FunctionType):
        value.__qualname__ = f"{cls.__qualname__}.{value.__name__}"
    return value


def generate_fast_dataclass(cls: Type[_T]) -> Type[_T]:
    """生成快速数据类"""

    # Now that dicts retain insertion order, there's no reason to use
    # an ordered dict.  I am leveraging that ordering here, because
    # derived class fields overwrite base class fields, but the order
    # is defined by the base class, which is found first.
    # 既然dicts保留了插入顺序，就没有理由使用一个有序的格言。
    # 我在这里利用这个有序，因为派生类字段覆盖基类字段，但顺序由基类定义，该基类首先找到。
    dataclass_fields = {}

    if cls.__module__ in sys.modules:
        _globals = sys.modules[cls.__module__].__dict__
    else:
        # Theoretically this can happen if someone writes
        # a custom string to cls.__module__.  In which case
        # such dataclass won't be fully introspectable
        # (w.r.t. typing.get_type_hints) but will still function
        # correctly.
        _globals = {}

    # 设置快速数据类的配置
    dataclass_config = getattr(cls, _DATACLASS_CONFIG_NAME, None)
    if dataclass_config is None:
        dataclass_config = DataclassConfig()
        setattr(cls, _DATACLASS_CONFIG_NAME, dataclass_config)

    # 设置快速数据类的序列化器
    fast_serializer = getattr(cls, _FAST_SERIALIZER_NAME, None)
    if fast_serializer is None:
        fast_serializer = FastSerializer()
        setattr(cls, _FAST_SERIALIZER_NAME, fast_serializer)

    # Find our base classes in reverse MRO order, and exclude
    # ourselves.  In reversed order so that more derived classes
    # override earlier field definitions in base classes.  As long as
    # we're iterating over them, see if any are frozen.
    # 以相反的MRO顺序查找我们的基类，并排除我们自己以相反的顺序，使更多的派生类重写基类中早期的字段定义。
    # 只要我们正在对它们进行迭代，看看是否有冻结的。

    # any_frozen_base = False
    # has_dataclass_bases = False
    for base in cls.__mro__[-1:0:-1]:
        # Only process classes that have been processed by our
        # decorator.  That is, they have a _FIELDS attribute.
        base_fields = getattr(base, _DATACLASS_FIELDS_NAME, None)
        if base_fields:
            has_dataclass_bases = True
            for _field in base_fields.values():
                dataclass_fields[_field.name] = _field
                cls.__annotations__[_field.name] = _field.type
                setattr(cls, _field.name, _field)  # 让未实例时获取为字段信息
            # if getattr(base, _DATACLASS_CONFIG_NAME).frozen:
            #     any_frozen_base = True

    # Annotations that are defined in this class (not in base
    # classes).  If __annotations__ isn't present, then this class
    # adds no new annotations.  We use this to compute fields that are
    # added by this class.
    #
    # Fields are found from cls_annotations, which is guaranteed to be
    # ordered.  Default values are from class attributes, if a field
    # has a default.  If the default value is a Field(), then it
    # contains additional info beyond (and possibly including) the
    # actual default value.  Pseudo-fields ClassVars and InitVars are
    # included, despite the fact that they're not real fields.  That's
    # dealt with later.
    # 此类中定义的注释（不在基类中类）。如果__annotations__不存在，则此类不添加新的注释。我们使用它来计算由此类添加。
    # 字段是从cls_annotations中找到的，保证为命令。默认值来自类属性，如果字段具有默认值。
    # 如果默认值是Field（），则它包含超出（可能包括）的其他信息实际默认值。伪字段ClassVars和InitVars是 包括在内，尽管它们不是真正的领域。
    # 那是稍后处理。
    cls_annotations = cls.__dict__.get('__annotations__', {})

    # Now find fields in our class.  While doing so, validate some
    # things, and set the default values (as class attributes) where we can.
    # 现在在我们班上查找字段。在这样做的同时，验证一些并设置默认值（作为类属性），其中我们可以。
    cls_fields = [_generate_field(cls, name, annotation, dataclass_config) for name, annotation in cls_annotations.items()]
    [dataclass_fields.__setitem__(_field.name, _field) for _field in cls_fields]  # type: ignore

    # Do we have any Field members that don't also have annotations?
    # 我们有没有字段成员也没有注释？
    for field_name, value in cls.__dict__.items():
        if isinstance(value, Field) and field_name not in cls_annotations:
            raise TypeError(f'{field_name!r} is a field but has no type annotation')

    # Remember all the fields on our class (including bases).  This
    # also marks this class as being a dataclass.
    # 记住我们班上的所有字段（包括基数）。这还将该类标记为数据类。
    setattr(cls, _DATACLASS_FIELDS_NAME, dataclass_fields)

    # 设置装饰器们
    dataclass_decorators = FastDataclassDecoratorInfo.build(cls)
    setattr(cls, _FAST_DATACLASS_DECORATORS_NAME, dataclass_decorators)

    # Was this class defined with an explicit __hash__?  Note that if
    # __eq__ is defined in this class, then python will automatically
    # set __hash__ to None.  This is a heuristic, as it's possible
    # that such a __hash__ == None was not auto-generated, but it
    # closes enough.
    # class_hash = cls.__dict__.get('__hash__', None)
    # has_explicit_hash = not (class_hash is None or (class_hash is None and '__eq__' in cls.__dict__))

    # If we're generating ordering methods, we must be generating the
    # eq methods.
    if dataclass_config.order and not dataclass_config.eq:
        raise ValueError('eq must be true if order is true')

    # Get the fields as a list, and include only real fields.  This is
    # used in all the following methods.
    # field_list = [f for f in dataclass_fields.values() if getattr(f, '_field_type', None) is _BASE_FIELD]

    # if dataclass_config.repr:
    #     _fields = [f for f in field_list if f.repr]
    #     _set_new_attribute(cls, '__repr__', _repr_fn(_fields, globals))

    # Decide if/how we're going to create a hash function.
    # hash_action = _hash_action[bool(dataclass_config.unsafe_hash), bool(dataclass_config.eq), bool(dataclass_config.frozen),
    #                            has_explicit_hash]
    # if hash_action:
    #     # No need to call _set_new_attribute here, since by the time
    #     # we're here the overwriting is unconditional.
    #     cls.__hash__ = hash_action(cls, field_list, _globals)
    #
    # if not getattr(cls, '__doc__'):
    #     # Create a class doc-string.
    #     try:
    #         # In some cases fetching a signature is not possible.
    #         # But, we surely should not fail in this case.
    #         text_sig = str(inspect.signature(cls)).replace(' -> None', '')
    #     except (TypeError, ValueError):
    #         text_sig = ''
    #     cls.__doc__ = (cls.__name__ + text_sig)

    return cls


# @dataclass_transform(kw_only_default=True, field_specifiers=(Field,))
class FastDataclassMeta(type):

    def __new__(cls, name, bases, dct, **kwargs):
        if not bases:
            # This is the FastDataclass class itself being created and does not require any logic
            # 这是正在创建的快速数据类本身，不需要任何逻辑
            return super().__new__(cls, name, bases, dct, **kwargs)

        _cls: Type['FastDataclass'] = super().__new__(cls, name, bases, dct, **kwargs)  # type: ignore

        return generate_fast_dataclass(_cls)


class FastDataclass(metaclass=FastDataclassMeta):
    """Base class for creating fast dataclass 用于创建快速数据类的基类"""

    """数据类配置"""
    dataclass_config: ClassVar[DataclassConfig]

    """在数据类上定义的字段的元数据"""
    dataclass_fields: ClassVar[Dict[str, Field]]

    """用于存放数据类的装饰器数据"""
    # __fast_dataclass_decorators__: ClassVar[FastDataclassDecoratorInfo]

    """JsonSchema"""
    # __fast_schema__: ClassVar[JsonSchema] = JsonSchema()

    """快速序列化器，支持反序列化和序列化"""
    __fast_serializer__: ClassVar[FastSerializer]

    def __init__(self, /, **kwargs):
        # 隐藏特定代码的回溯信息，以便在发生异常时，使回溯信息更加简洁和有意义。
        __tracebackhide__ = True
        self.__fast_serializer__.deserialize(kwargs, instance=self)

    def __post_init__(self):
        """
        Override this method to perform additional initialization after `__init__``.
        重写此方法以在`__init之后执行附加初始化__`，这将非常有用。
        """
        pass

    # def schema_dict(self):
    #     raise NotImplementedError('')

    def __str__(self):
        return f"{self.__class__.__name__}({self.__repr_names__(', ')})"

    def __repr__(self) -> str:
        return self.__str__()

    def __repr_names__(self, join_str: str):
        return join_str.join(repr(v) if a is None else f'{a}={v!r}' for a, v in self.__repr_values__())

    def __repr_values__(self):
        for k, v in self.__dict__.items():
            field = self.dataclass_fields.get(k)
            if field and field.repr:
                yield k, v
