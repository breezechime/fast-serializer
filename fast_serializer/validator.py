# -*- coding:utf-8 -*-
import collections.abc
import datetime
import decimal
import enum
import inspect
import re
import time
import typing_extensions
import uuid
from abc import ABC, abstractmethod
from decimal import Decimal
from types import FunctionType
from typing import (
    Any, Generator, Union, Collection, Iterable, Literal, List, get_args, Tuple, Set, Dict, Optional,
    Sequence, Mapping, Callable, TypedDict, FrozenSet, Type, Deque, is_typeddict
)
from .constants import _T
from .exceptions import DataclassCustomError, ErrorDetail, ValidationError, ValidatorBuildingError
from .type_parser import type_parser
from .types import optional
from .utils import _format_type, get_sub_validator_kwargs, isinstance_safe, issubclass_safe


class Validator(ABC):
    """验证器基类"""

    validator_name: str
    annotation: _T

    def __init__(self, **kwargs): ...

    @abstractmethod
    def validate(self, value): ...

    @property
    def name(self) -> str:
        return self.validator_name

    def __repr__(self):
        return f"{self.__class__.__name__}(\n  name: {self.name!r},\n  annotation: {self.annotation}\n)"

    @classmethod
    def build(cls, annotation: _T, **kwargs) -> 'Validator':
        return cls(annotation=annotation, **kwargs)


class AnyValidator(Validator):
    """任意类型验证器"""

    validator_name = 'any'
    annotation = Any

    def validate(self, value):
        return value


class StringValidator(Validator):
    """字符串验证器"""

    validator_name = 'str'
    annotation = str
    allow_number: bool = True

    def __init__(self, allow_number: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.allow_number = allow_number

    def validate(self, value, allow_number: bool = None) -> str:
        self.allow_number = self.allow_number if allow_number is None else allow_number
        maybe_str = self.maybe_str(value)
        if maybe_str:
            return maybe_str
        elif isinstance_safe(value, bytearray):
            return value.decode('utf-8')
        numbers_types = (IntegerValidator.annotation, FloatValidator.annotation,
                         DecimalValidator.annotation, BoolValidator.annotation)
        if self.allow_number and isinstance_safe(value, numbers_types):
            return self.annotation(value)
        raise ValueError('输入应为有效字符串')

    @classmethod
    def maybe_str(cls, value, raise_error: bool = True) -> optional[str]:
        if isinstance_safe(value, cls.annotation):
            return value
        elif isinstance_safe(value, BytesValidator.annotation):
            try:
                return value.decode('utf-8')
            except UnicodeDecodeError:
                if not raise_error:
                    return False
                raise DataclassCustomError('string_unicode', '输入应为有效字符串，不能将原始数据解析为unicode字符串')
        return None


class BoolValidator(Validator):
    """布尔验证器"""

    validator_name = 'bool'
    annotation = bool

    def validate(self, value) -> bool:
        if isinstance_safe(value, self.annotation):
            return value
        elif isinstance_safe(value, IntegerValidator.annotation):
            return self.int_to_bool(value)
        elif isinstance_safe(value, FloatValidator.annotation):
            return self.int_to_bool(IntegerValidator.annotation(value))
        elif isinstance_safe(value, StringValidator.annotation):
            return self.str_to_bool(value)
        raise ValueError('输入应为有效布尔类型')

    @staticmethod
    def str_to_bool(value: str) -> bool:
        if value.lower() in ['0', 'false', 'f', 'n', 'no', 'off', '不', '否', '错误', '异常', '错']:
            return False
        elif value.lower() in ['1', 'true', 't', 'y', 'yes', 'on', '是', '好', '好的', '正确', '对', '对的']:
            return True
        raise ValueError('输入应为有效布尔类型')

    @staticmethod
    def int_to_bool(value: int) -> bool:
        if value == 0:
            return False
        elif value == 1:
            return True
        raise ValueError('输入应为有效布尔类型')


class IntegerValidator(Validator):
    """整型验证器"""

    validator_name = 'int'
    annotation = int
    half_adjust_value = 0.11

    def validate(self, value):
        if isinstance_safe(value, self.annotation):
            return value
        try:
            maybe_str = StringValidator.maybe_str(value)
            if maybe_str:
                return int(value)
        except (UnicodeDecodeError, ValueError, DataclassCustomError):
            raise DataclassCustomError('int_parsing', '输入应为有效整数，无法将字符串解析为整数')
        if isinstance_safe(value, (float, Decimal)):
            return self.float_or_decimal_to_int(value)
        try:
            if issubclass_safe(value, enum.Enum):
                return self.enum_to_int(value)
        except (ValueError, TypeError):
            raise ValueError('输入应为有效整数')
        raise ValueError('输入应为有效整数')

    @staticmethod
    def bool_to_int(value: bool):
        return IntegerValidator.annotation(value)

    @staticmethod
    def str_to_int(value: str):
        return IntegerValidator.annotation(value)

    def float_or_decimal_to_int(self, value: float, is_decimal: bool = False):
        # 四舍五入容差
        integer_part = self.annotation(value)
        maybe_int = self.annotation(self.annotation(value + self.half_adjust_value if not is_decimal
                                                    else Decimal(self.half_adjust_value)))
        return maybe_int if maybe_int > integer_part else integer_part

    @staticmethod
    def enum_to_int(value: enum.Enum):
        return int(value.value)


class FloatValidator(Validator):
    """浮点验证器"""

    validator_name = 'float'
    annotation = float

    def validate(self, value):
        if isinstance_safe(value, self.annotation):
            return value
        elif isinstance_safe(value, IntegerValidator.annotation):
            return self.annotation(value)
        elif isinstance_safe(value, DecimalValidator.annotation):
            return self.annotation(value)
        try:
            maybe_str = StringValidator.maybe_str(value)
            if maybe_str:
                return self.annotation(value)
        except (UnicodeDecodeError, ValueError, TypeError, DataclassCustomError):
            raise DataclassCustomError('float_parsing', '输入应为有效数字，无法将字符串解析为数字')
        raise DataclassCustomError('float_parsing', '输入应为有效浮点值')


class DecimalValidator(FloatValidator):
    """Decimal验证器"""

    validator_name = 'decimal'
    annotation = Decimal

    def validate(self, value):
        if isinstance_safe(value, self.annotation):
            return value
        elif isinstance_safe(value, IntegerValidator.annotation):
            return self.annotation(value)
        elif isinstance_safe(value, FloatValidator.annotation):
            # 防止精度过长
            return self.annotation(StringValidator.annotation(value))
        try:
            maybe_str = StringValidator.maybe_str(value)
            if maybe_str:
                return self.annotation(value)
        except (UnicodeDecodeError, ValueError, TypeError, DataclassCustomError, decimal.InvalidOperation):
            raise DataclassCustomError('decimal_parsing', '输入应为有效数值')
        raise DataclassCustomError('decimal_parsing', '输入应为有效数值')


class BytesValidator(Validator):
    """字节验证器"""

    validator_name = 'bytes'
    annotation = bytes

    def validate(self, value):
        if isinstance_safe(value, self.annotation):
            return value
        elif isinstance_safe(value, StringValidator.annotation):
            return value.encode('utf-8')
        elif isinstance_safe(value, bytearray):
            return self.annotation(value)
        raise ValueError('输入应为有效字节类型')


class IsInstanceValidator(Validator):
    """目标实例验证器"""

    validator_name = 'is_instance'

    def __init__(self, annotation: _T, **kwargs):
        super().__init__(**kwargs)
        self.annotation = annotation

    def validate(self, value):
        if isinstance_safe(value, self.annotation):
            return value
        raise ValueError(f'输入应为`{_format_type(self.annotation)}`实例')

    @property
    def name(self) -> str:
        return f"{self.validator_name}[{_format_type(self.annotation)}]"


class IsSubClassValidator(Validator):
    """目标类或子类验证器"""

    validator_name = 'is_subclass'

    def __init__(self, annotation: _T, **kwargs):
        super().__init__(**kwargs)
        self.annotation = annotation

    def validate(self, value):
        if issubclass_safe(value, self.annotation):
            return value
        raise DataclassCustomError('is_subclass', f'输入应该是`{_format_type(self.annotation)}`的子类')

    @property
    def name(self) -> str:
        return f"{self.validator_name}[{_format_type(self.annotation)}]"

    @classmethod
    def build(cls, annotation: _T, **kwargs) -> 'IsSubClassValidator':
        args = get_args(annotation)
        return cls(annotation=args[0], **kwargs)


class OptionalValidator(Validator):
    """可空类型验证器"""

    validator_name = 'optional'
    annotation = optional
    validator: Validator

    def __init__(self, validator: Validator, **kwargs):
        super().__init__(**kwargs)
        self.validator = validator

    def validate(self, value):
        if value is None:
            return value
        return self.validator.validate(value)

    @classmethod
    def build(cls, annotation: _T, **kwargs):
        if not type_parser.is_optional(annotation):
            annotation = Optional[annotation]
        validator = matching_validator(get_args(annotation)[0], **kwargs)
        return cls(validator=validator, **kwargs)

    @property
    def name(self) -> str:
        return f"{self.validator_name}[{self.validator.name}]"


class UnionValidator(Validator):
    """联合类型验证器"""

    validator_name = 'union'
    annotation = Union
    validators: List[Validator]

    def __init__(self, validators: List[Validator], **kwargs):
        super().__init__(**kwargs)
        self.validators = validators

    def validate(self, value):
        err: optional[ErrorDetail] = None
        for validator in self.validators:
            errs: List[ErrorDetail] = []
            v = catch_validate_error(value, validator, [], errs)
            if not errs:
                return v
            err = errs[-1]
        raise DataclassCustomError(err.exception_type, err.msg)

    @classmethod
    def build(cls, annotation: _T, **kwargs):
        args = get_args(annotation)
        if not args:
            raise ValidatorBuildingError(f"使用Union注解至少需要有一种类型才可构建 {cls.__name__}")
        if not type_parser.is_union(annotation):
            raise ValidatorBuildingError(f"输入应为Union注解才可构建 {cls.__name__}")
        validators = [matching_validator(sub, **get_sub_validator_kwargs(kwargs, i)) for i, sub in enumerate(args)]
        return cls(validators=validators, **kwargs)

    @property
    def name(self) -> str:
        return f"{self.validator_name}[{', '.join([val.name for val in self.validators])}]"


class LiteralValidator(Validator):
    """字面量类型验证器"""

    validator_name = 'literal'
    annotation = Literal
    expected_values: Tuple[Any, ...]

    def __init__(self, *expected: Tuple[Any, ...], **kwargs):
        super().__init__(**kwargs)
        self.expected_values = expected

    def validate(self, value):
        if value in self.expected_values:
            return value
        raise ValueError(f'输入应为 {self.format_expected_values}')

    @classmethod
    def build(cls, annotation, **kwargs):
        if not type_parser.is_literal(annotation):
            raise ValueError(f"输入应为Literal注解才可构建 {cls.__name__}")
        args = get_args(annotation)
        return cls(*args)

    def __repr__(self):
        return (f"{self.__class__.__name__}("
                f"\n  name: {self.name}"
                f"\n  annotation: {self.annotation}"
                f"\n  values: {self.expected_values}"
                f"\n)")

    @property
    def name(self) -> str:
        return f'{self.validator_name}[{",".join([f"{value!r}" for value in self.expected_values])}]'

    @property
    def format_expected_values(self):
        return f'{", ".join([f"`{value!r}`" for value in self.expected_values])}'


# TODO
class FastDataclassValidator(Validator):
    """快速数据类验证器"""

    validator_name = 'fast_dataclass'

    def __init__(self, annotation: _T, **kwargs):
        super().__init__(**kwargs)
        self.annotation = annotation

    def validate(self, value):
        if isinstance_safe(value, self.annotation):
            return value
        if isinstance_safe(value, dict):
            return self.annotation(**value)
        # TODO from obj
        raise NotImplementedError('error')
        # return self.annotation

    @property
    def name(self) -> str:
        return _format_type(self.annotation)

    @classmethod
    def build(cls, annotation: _T, **kwargs) -> 'FastDataclassValidator':
        if not type_parser.is_fast_dataclass(annotation):
            raise DataclassCustomError('fast_dataclass_parsing', '输入应为快速数据类')
        return cls(annotation=annotation, **kwargs)


class PydanticModelValidator(Validator):
    """Pydantic模型验证器"""

    validator_name = 'pydantic'
    annotation = None

    def validate(self, value):
        if type_parser.is_pydantic_model(value):
            return value
        raise ValueError('输入应为Pydantic模型')

    @classmethod
    def build(cls, annotation: _T, **kwargs) -> 'PydanticModelValidator':
        try:
            from pydantic import BaseModel
        except ImportError:
            raise ImportError('导入Pydantic失败, 可能未安装')
        if not type_parser.is_pydantic_model(annotation):
            raise ValueError('输入应为Pydantic模型')
        return cls(annotation=annotation, **kwargs)


# TODO
class DataclassValidator(Validator):
    """数据类验证器"""

    validator_name = 'dataclass'

    def validate(self, value):
        try:
            from dataclasses import is_dataclass
        except ImportError:
            raise ImportError('导入Dataclass失败, 您把它删了吗？')
        if is_dataclass(value):
            return value
        raise ValueError('输入应为Dataclass数据类')


class DictValidator(Validator):
    """字典验证器"""

    validator_name = 'dict'
    annotation = dict
    key_validator: Validator
    value_validator: Validator
    min_length: optional[int]
    max_length: optional[int]

    def __init__(self, key_validator: Validator, value_validator: Validator, min_length: optional[int] = None,
                 max_length: optional[int] = None, **kwargs):
        super().__init__(**kwargs)
        self.key_validator = key_validator
        self.value_validator = value_validator
        self.min_length = min_length
        self.max_length = max_length

    def validate(self, value):
        if not isinstance_safe(value, Mapping):
            raise DataclassCustomError('dict_type', '输入应为有效键值对')
        # 验证长度
        length = len(value)
        check_collection_length(self.annotation, length, self.min_length, self.max_length)
        # 优化（双any可省略很多验证性能）
        key_validator_is_any = self.key_validator.annotation is Any
        value_validator_is_any = self.value_validator.annotation is Any
        if key_validator_is_any and value_validator_is_any:
            return value
        errs: List[ErrorDetail] = []
        # 验证keys(any优化)
        if key_validator_is_any:
            keys = value.keys()
        else:
            keys = [catch_validate_error(v, self.key_validator, [i], errs) for i, v in enumerate(value.keys())]
        # 验证values
        if value_validator_is_any:
            values = value.values()
        else:
            values = [catch_validate_error(v, self.value_validator, [i], errs) for i, v in enumerate(value.values())]
        res_dict = self.annotation(zip(keys, values))
        return res_dict

    @classmethod
    def build(cls, annotation: _T, **kwargs) -> 'DictValidator':
        _args = get_args(annotation)
        _args_length = len(_args)
        key_validator = matching_validator(_args[0], **kwargs) if _args_length >= 1 else BASE_VALIDATORS[Any]
        value_validator = matching_validator(_args[1], **kwargs) if _args_length >= 2 else BASE_VALIDATORS[Any]
        return cls(key_validator, value_validator, *_args, **kwargs)

    @property
    def name(self) -> str:
        return f'{self.validator_name}[{self.key_validator.name}, {self.value_validator.name}]'


class TypedDictField:
    name: str
    required: bool
    validator: Validator

    def __init__(self, name: str, required: bool, validator: Validator,):
        self.name = name
        self.required = required
        self.validator = validator

    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.name}, required={self.required}, validator={self.validator})"


class TypedDictValidator(Validator):
    """带类型字典验证器"""

    validator_name = 'typed_dict'
    annotation = TypedDict
    fields: Dict[str, TypedDictField]

    def __init__(self, fields: Dict[str, TypedDictField], **kwargs):
        super().__init__(**kwargs)
        self.fields = fields

    def validate(self, value):
        if not isinstance_safe(value, Mapping):
            raise DataclassCustomError('dict_type', '输入应为有效键值对')
        errs: List[ErrorDetail] = []
        result: dict = {
            field_name: self.typed_dict_catch_validate_error(value, field, value.get(field_name), errs)
            for field_name, field in self.fields.items()
        }
        if errs:
            raise ValidationError(title=self.name, line_errors=errs)
        return result

    @staticmethod
    def typed_dict_catch_validate_error(origin_v, field, v, errs):
        # 必填
        if v is None and field.required:
            err = ErrorDetail(
                loc=[field.name],
                input_value=origin_v,
                exception_type='missing',
                msg='字段为必填项'
            )
            errs.append(err)
            return v
        return catch_validate_error(v, field.validator, [field.name], errs)

    @classmethod
    def build(cls, annotation: _T, **kwargs) -> 'TypedDictValidator':
        fields: Dict[str, TypedDictField] = dict()
        for k, field_name in enumerate(annotation.__annotations__):
            anno = annotation.__annotations__[field_name]
            required = True
            # 可空
            if type_parser.is_optional(anno):
                required = False
            validator = matching_validator(anno, **get_sub_validator_kwargs(kwargs))
            field = TypedDictField(field_name, required, validator)
            fields[field_name] = field
        return cls(fields=fields, **kwargs)


class ListValidator(Validator):
    """列表验证器"""

    validator_name = 'list'
    annotation = list
    item_validator: Validator
    min_length: optional[int]
    max_length: optional[int]

    def __init__(self, item_validator: Validator, min_length: optional[int] = None, max_length: optional[int] = None,
                 **kwargs):
        super().__init__(**kwargs)
        self.item_validator = item_validator
        self.min_length = min_length
        self.max_length = max_length

    def validate(self, value):
        collection = extract_collection(value, 'list_type', '列表')
        # 验证长度
        check_collection_length(self.annotation, len(collection), self.min_length, self.max_length)
        # 优化
        if self.item_validator.annotation is Any:
            is_list = isinstance_safe(collection, list)
            return collection if is_list else self.annotation(collection)
        errs: List[ErrorDetail] = []
        result: list = [
            catch_validate_error(item, self.item_validator, [i], errs)
            for i, item in enumerate(collection)
        ]
        if errs:
            raise ValidationError(title=self.name, line_errors=errs)
        return result

    @classmethod
    def build(cls, annotation: _T, **kwargs) -> 'ListValidator':
        args = get_args(annotation)
        sub_annotation = args[0] if args else Any
        item_validator = matching_validator(sub_annotation, **get_sub_validator_kwargs(kwargs))
        return cls(item_validator=item_validator, **kwargs)

    @property
    def name(self) -> str:
        return f'{self.validator_name}[{self.item_validator.name}]'


class TupleValidator(Validator):
    """元组验证器"""

    validator_name = 'tuple'
    annotation = tuple
    validators: List[Validator]
    variadic: bool = True
    min_length: optional[int]
    max_length: optional[int]

    def __init__(self, validators: List[Validator], variadic: bool = False, min_length: optional[int] = None,
                 max_length: optional[int] = None, **kwargs):
        super().__init__(**kwargs)
        self.validators = validators
        self.variadic = variadic
        self.min_length = min_length
        self.max_length = max_length

    def validate(self, value):
        collection = extract_collection(value, 'tuple_type', '元祖')
        # 检查长度
        length = len(collection)
        check_collection_length(self.annotation, length, self.min_length, self.max_length)
        errs: List[ErrorDetail] = []
        # 不是无限延伸的元祖
        if not self.variadic:
            should_be_length = len(self.validators)
            if length > should_be_length:
                raise DataclassCustomError(
                    'too_long',
                    f'验证后元组最多应包含{should_be_length}个项目，而不是{length}个'
                )
            result: list = []
            for i, val in enumerate(self.validators):
                try:
                    v = collection[i]
                    result.append(catch_validate_error(v, val, [i], errs))
                except IndexError:
                    errs.append(ErrorDetail([i], collection, 'missing', '字段为必填项'))
            if errs:
                raise ValidationError(title=self.name, line_errors=errs)
            return tuple(result)
        # 可变
        validator = self.validators[0]
        result: tuple = tuple(
            catch_validate_error(item, validator, [i], errs)
            for i, item in enumerate(collection)
        )
        if errs:
            raise ValidationError(title=self.name, line_errors=errs)
        return result

    @classmethod
    def build(cls, annotation: _T, **kwargs) -> 'TupleValidator':
        args = get_args(annotation)
        if Ellipsis in args:
            variadic = True
            args = list(args)
            args.remove(Ellipsis)
        else:
            variadic = False
        validators = [matching_validator(sub, **get_sub_validator_kwargs(kwargs, i)) for i, sub in enumerate(args)]
        if not validators:
            validators = [BASE_VALIDATORS[Any]]
            variadic = True
        if variadic and len(validators) > 1:
            raise ValidatorBuildingError(f'可变元组只能有一种类型')
        return cls(validators=validators, variadic=variadic, **kwargs)

    @property
    def name(self) -> str:
        return f'{self.validator_name}[{", ".join([val.name for val in self.validators])}]'


class SetValidator(Validator):
    """集合验证器"""

    validator_name = 'set'
    annotation = set
    item_validator: Validator
    min_length: optional[int]
    max_length: optional[int]

    def __init__(self, item_validator: optional[Validator] = None, min_length: optional[int] = None,
                 max_length: optional[int] = None, **kwargs):
        super().__init__(**kwargs)
        self.item_validator = item_validator or BASE_VALIDATORS[Any]
        self.min_length = min_length
        self.max_length = max_length

    def validate(self, value):
        collection = extract_collection(value, 'set_type', '集合')
        # 检查长度
        check_collection_length(self.annotation, len(collection), self.min_length, self.max_length)
        # 优化
        if self.item_validator.annotation is Any:
            is_set = isinstance_safe(collection, self.annotation)
            return collection if is_set else self.annotation(collection)
        errs: List[ErrorDetail] = []
        result: set = {
            catch_validate_error(item, self.item_validator, [i], errs)
            for i, item in enumerate(collection)
        }
        if errs:
            raise ValidationError(title=self.name, line_errors=errs)
        return result

    @classmethod
    def build(cls, annotation: _T, **kwargs) -> 'SetValidator':
        args = get_args(annotation)
        sub_annotation = args[0] if args else Any
        item_validator = matching_validator(sub_annotation, **get_sub_validator_kwargs(kwargs))
        return cls(item_validator=item_validator, **kwargs)

    @property
    def name(self) -> str:
        return f'{self.validator_name}[{self.item_validator.name}]'


class FrozenValidator(Validator):
    """冻结集合验证器"""

    validator_name = 'frozenset'
    annotation = frozenset
    item_validator: Validator
    min_length: optional[int]
    max_length: optional[int]

    def __init__(self, item_validator: Validator, min_length: optional[int] = None, max_length: optional[int] = None,
                 **kwargs):
        super().__init__(**kwargs)
        self.item_validator = item_validator
        self.min_length = min_length
        self.max_length = max_length

    def validate(self, value):
        collection = extract_collection(value, 'frozenset_type', '冻结集合')
        # 检查长度
        check_collection_length(self.annotation, len(collection), self.min_length, self.max_length)
        # 优化
        if self.item_validator.annotation is Any:
            is_set = isinstance_safe(collection, self.annotation)
            return collection if is_set else self.annotation(collection)
        errs: List[ErrorDetail] = []
        result: frozenset = frozenset({
            catch_validate_error(item, self.item_validator, [i], errs)
            for i, item in enumerate(collection)
        })
        if errs:
            raise ValidationError(title=self.name, line_errors=errs)
        return result

    @classmethod
    def build(cls, annotation: _T, **kwargs) -> 'FrozenValidator':
        args = get_args(annotation)
        sub_annotation = args[0] if args else Any
        item_validator = matching_validator(sub_annotation, **get_sub_validator_kwargs(kwargs))
        return cls(item_validator=item_validator, **kwargs)

    @property
    def name(self) -> str:
        return f'{self.validator_name}[{self.item_validator.name}]'


class DequeValidator(Validator):
    """队列验证器"""

    validator_name = 'deque'
    annotation = collections.deque
    item_validator: Validator
    min_length: optional[int]
    max_length: optional[int]

    def __init__(self, item_validator: Validator, min_length: optional[int] = None, max_length: optional[int] = None,
                 **kwargs):
        super().__init__(**kwargs)
        self.item_validator = item_validator
        self.min_length = min_length
        self.max_length = max_length

    def validate(self, value) -> collections.deque:
        collection = extract_collection(value, 'deque_type', '队列')
        # 检查长度
        check_collection_length(self.annotation, len(collection), self.min_length, self.max_length)
        # 优化
        if self.item_validator.annotation is Any:
            is_deque = isinstance_safe(collection, self.annotation)
            return collection if is_deque else self.annotation(collection)
        errs: List[ErrorDetail] = []
        result: collections.deque = collections.deque((
            catch_validate_error(item, self.item_validator, [i], errs)
            for i, item in enumerate(collection)
        ))
        if errs:
            raise ValidationError(title=self.name, line_errors=errs)
        return result

    @classmethod
    def build(cls, annotation: _T, **kwargs) -> 'DequeValidator':
        args = get_args(annotation)
        item_validator = matching_validator(args[0], **get_sub_validator_kwargs(kwargs)) \
            if args else BASE_VALIDATORS[Any]
        return cls(item_validator=item_validator, **kwargs)

    @property
    def name(self) -> str:
        return f'{self.validator_name}[{self.item_validator.name}]'


class GeneratorValidator(Validator):
    """生成器验证器"""

    validator_name = 'generator'
    annotation = Generator
    item_validator: Validator
    min_length: optional[int]
    max_length: optional[int]

    def __init__(self, item_validator: Validator, min_length: optional[int] = None, max_length: optional[int] = None,
                 **kwargs):
        super().__init__(**kwargs)
        self.item_validator = item_validator
        self.min_length = min_length
        self.max_length = max_length

    def validate(self, value):
        if not isinstance_safe(value, Iterable):
            raise DataclassCustomError('iterable_type', '输入应为可迭代类型')
        iterator = GeneratorIterator(
            iterable=(v for v in value),
            validator=self.item_validator,
            min_length=self.min_length,
            max_length=self.max_length,
        )
        return iterator

    @property
    def name(self) -> str:
        return f"{self.validator_name}[{_format_type(self.item_validator.name)}]"

    @classmethod
    def build(cls, annotation: _T, **kwargs) -> 'GeneratorValidator':
        args = get_args(annotation)
        sub_annotation = args[0] if args else Any
        item_validator = matching_validator(sub_annotation, **get_sub_validator_kwargs(kwargs))
        return cls(item_validator=item_validator, **kwargs)


class GeneratorIterator:
    """生成器迭代器，包含验证"""
    iterable: Generator
    validator: Validator
    min_length: optional[int]
    max_length: optional[int]
    index: int

    def __init__(self, iterable: Generator, validator: Validator, min_length: optional[int] = None,
                 max_length: optional[int] = None):
        self.iterable = iterable
        self.validator = validator
        self.min_length = min_length
        self.max_length = max_length
        self.index = 0

    def __iter__(self):
        return self.iterable

    def __next__(self):
        value = next(self.iterable)
        errs: List[ErrorDetail] = []
        value = catch_validate_error(value, self.validator, [self.index], errs)
        # 检查长度
        try:
            check_collection_length(Generator, self.index + 1, self.min_length, self.max_length)
        except DataclassCustomError as e:
            errs.append(ErrorDetail([self.index], value, e.exception_type, e.msg))
        if errs:
            raise ValidationError(title=self.__class__.__name__, line_errors=errs)
        self.index += 1
        return value

    def __repr__(self):
        return f"{self.__class__.__name__}(index={self.index}, validator={self.validator.name})"

    def __str__(self):
        return self.__repr__()


class ArgumentValidatorParameter:
    """参数验证器参数"""

    name: str
    validator: Validator


class ArgumentsValidator(Validator):
    """参数验证器"""

    validator_name = 'arguments'
    parameters: Dict[str, ArgumentValidatorParameter]
    positional_params_count: int = 0
    var_args_validator: optional[Validator]
    var_kwargs_validator: optional[Validator]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def validate(self, value):
        pass

    @classmethod
    def build(cls, annotation: _T, **kwargs) -> 'ArgumentsValidator':
        pass


class FunctionValidator(Validator):
    """函数验证器，传递函数参数自动调用函数"""

    validator_name = 'function'
    annotation = FunctionType
    """参数验证器列表"""
    argument_validator: Validator
    function: FunctionType

    def __init__(self, function: FunctionType, **kwargs):
        super().__init__(**kwargs)
        # self.argument_validator = argument_validator
        self.function = function

    def validate(self, value):
        is_dict = isinstance(value, dict)
        if not isinstance_safe(value, (tuple, list)) and not is_dict:
            raise DataclassCustomError('arguments_type', '参数必须是元组、列表或字典')
        parameters = inspect.signature(self.function).parameters
        errs: List[ErrorDetail] = []
        for index, param_name in enumerate(parameters):
            parameter = parameters[param_name]
            try:
                if is_dict:
                    input_value = value[param_name]
                else:
                    input_value = value[index]
            except KeyError:
                err = ErrorDetail(
                    [param_name],
                    value,
                    'missing',
                    '字段不能为空'
                )
                errs.append(err)
                continue
            except IndexError:
                err = ErrorDetail(
                    [index],
                    value,
                    'missing',
                    '字段不能为空'
                )
                errs.append(err)
                continue
            if input_value is None and parameter.default == inspect.Parameter.empty:
                err = ErrorDetail(
                    [param_name],
                    value,
                    'missing',
                    '字段不能为空'
                )
                errs.append(err)
                continue
        if errs:
            raise ValidationError(title=self.name, line_errors=errs)

    def __repr__(self):
        return (f"{self.__class__.__name__}(\n  "
                f"name: {self.name!r},\n  "
                f"function: {self.function}\n  "
                f"argument_validator: {self.argument_validator}"
                f")")

    @classmethod
    def build(cls, annotation: _T, **kwargs) -> 'FunctionValidator':
        is_function = type_parser.is_function(annotation)
        if not is_function:
            raise DataclassCustomError('func_building', '输入应为函数才可构建函数验证器')
        return cls(function=annotation, **kwargs)


class CallableValidator(Validator):
    """可调用类型验证器，验证是否可调用"""

    validator_name = 'callable'
    annotation = Callable

    def validate(self, value):
        try:
            if callable(value):
                return value
        except TypeError:
            raise DataclassCustomError('callable_type', '输入应为可调用类型')
        raise DataclassCustomError('callable_type', '输入应为可调用类型')


class DatetimeValidator(Validator):
    """日期时间验证器"""

    validator_name = 'datetime'
    annotation = datetime.datetime

    """年长度"""
    year_length = len(StringValidator.annotation(datetime.MAXYEAR))
    """月长度"""
    month_length = 2
    """日长度"""
    day_length = 2
    """总长度"""
    date_length = year_length + month_length + day_length
    """时间戳容忍值"""
    tolerance_value = 100
    """对比时间戳"""
    compare_timestamp = time.time()
    """时间戳长度"""
    timestamp_length = len(StringValidator.annotation(int(compare_timestamp)))

    def validate(self, value):
        if isinstance_safe(value, self.annotation):
            return value
        elif isinstance_safe(value, DateValidator.annotation):
            return self.date_to_datetime(value)
        try:
            if isinstance_safe(value, (IntegerValidator.annotation, FloatValidator.annotation)):
                return self.str_or_int_to_datetime(IntegerValidator.annotation(value))
            maybe_str = StringValidator.maybe_str(value, raise_error=False)
            if maybe_str:
                return self.str_or_int_to_datetime(maybe_str)
        except DataclassCustomError as e:
            raise e
        except (ValueError, TypeError) as e:
            raise self.get_default_error(StringValidator.annotation(e))
        raise self.get_default_error()

    @classmethod
    def get_default_error(cls, msg: optional[str] = None):
        return DataclassCustomError('datetime_parsing', msg or '输入应为有效的日期时间或日期')

    @classmethod
    def timestamp_to_datetime(cls, value: Union[int, float]) -> datetime.datetime:
        # 兼容毫秒级时间戳 下方为了兼容'1718245600000.0' 这种字符串带小数点的情况无法直接int
        if len(str(int(float(value)))) > cls.timestamp_length:
            value = value / 1000
        return datetime.datetime.fromtimestamp(value)

    @classmethod
    def date_to_datetime(cls, value: datetime.date) -> datetime.datetime:
        return datetime.datetime(year=value.year, month=value.month, day=value.day)

    @classmethod
    def str_or_int_to_datetime(cls, value: Union[str, int]):
        value = StringValidator.annotation(value)
        length = len(value)
        if length < cls.year_length:
            raise DataclassCustomError('datetime_parsing', '输入应为有效的日期时间或日期，输入太短')
        int_value = None
        try:
            int_value = int(float(value))  # 兼容'2024.0'
        except (ValueError, TypeError):
            pass
        if int_value and int_value < datetime.MAXYEAR:
            # e.g: 2024 4位最短
            return datetime.datetime(int_value, 1, 1)
        elif length == cls.date_length and int_value:
            # e.g: 20240204 8位无符号版本
            year = int(value[:cls.year_length])
            month = int(value[cls.year_length:6])
            day = int(value[cls.year_length + 2:])
            return datetime.datetime(year, month, day)
        elif length == cls.date_length + 2 and int_value:
            # e.g: 1718245600 时间戳10位版本
            return datetime.datetime.fromtimestamp(int_value)
        elif length == cls.date_length + 2 and int_value is None:
            # e.g: 2024-02-04 10位版本
            delimiter = cls.get_delimiter(value)
            __format = f'%Y{delimiter}%m{delimiter}%d'
            try:
                return datetime.datetime.strptime(value, __format)
            except (ValueError, TypeError):
                raise DataclassCustomError('date_parsing', f'时间数据“{value}”与格式“{__format}”不匹配')
        elif length == cls.date_length + 5 and int_value:
            # e.g: 1718245600000 时间戳13位版本
            return cls.timestamp_to_datetime(int_value)
        elif cls.date_length + 10 >= length >= cls.date_length + 6 and int_value:
            # e.g: 17182456.000 时间戳14-18位版本
            return cls.timestamp_to_datetime(int_value)
        elif length == cls.date_length + 8 and int_value is None:
            # e.g: 2024-02-04 10:15 16位版本
            delimiter = cls.get_delimiter(value)
            __format = f'%Y{delimiter}%m{delimiter}%d %H:%M'
            try:
                return datetime.datetime.strptime(value, __format)
            except (ValueError, TypeError):
                raise DataclassCustomError(
                    'datetime_parsing',
                    f'时间数据“{value}”与格式“{__format}”不匹配'
                )
        elif length == cls.date_length + 11 and int_value is None and 'T' not in value:
            # e.g: 2024-02-04 10:15:30
            delimiter = cls.get_delimiter(value)
            __format = f'%Y{delimiter}%m{delimiter}%d %H:%M:%S'
            try:
                return datetime.datetime.strptime(value, __format)
            except (ValueError, TypeError):
                raise DataclassCustomError(
                    'datetime_parsing',
                    f'时间数据“{value}”与格式“{__format}”不匹配'
                )
        elif length >= cls.date_length + 11 and int_value is None:
            # rfc3339格式支持
            try:
                return datetime.datetime.fromisoformat(value)
            except (ValueError, TypeError):
                raise DataclassCustomError(
                    'datetime_from_rfc3339_parsing',
                    '输入的RFC3339日期时间格式有误'
                )
        raise DatetimeValidator.get_default_error()

    @staticmethod
    def get_delimiter(value: str):
        return '/' if '/' in value else '.' if '.' in value else '-'


class TimeValidator(Validator):
    """时间验证器"""

    validator_name = 'time'
    annotation = datetime.time
    """模式：second模式数字当秒处理，time模式数字将转换时间，默认`second`"""
    mode: Literal['second', 'time']

    def __init__(self, mode: Literal['second', 'time'] = 'second', **kwargs):
        super().__init__(**kwargs)
        self.mode = mode

    def validate(self, value):
        if isinstance_safe(value, self.annotation):
            return value
        if isinstance_safe(value, DatetimeValidator.annotation):
            return value.time()
        elif isinstance_safe(value, IntegerValidator.annotation):
            return self.int_to_time(value)
        elif isinstance_safe(value, FloatValidator.annotation):
            return self.int_to_time(IntegerValidator.annotation(value))

        maybe_str = StringValidator.maybe_str(value, raise_error=False)
        if maybe_str:
            return self.str_to_time(maybe_str)
        raise self.get_default_error()

    def int_to_time(self, value: int) -> datetime.time:
        if self.mode == 'second':
            hour = value // 3600
            minute = value // 60
            second = value % 60
            return datetime.time(hour, minute, second)
        str_value = str(value)
        length = len(str_value)
        if length == 3:
            return datetime.time(int(str_value[0]), int(str_value[1:]), 0)
        elif length == 4:
            return datetime.time(int(str_value[:2]), int(str_value[2:]), 0)
        raise self.get_default_error()

    @classmethod
    def str_to_time(cls, value: str) -> datetime.time:
        length = len(value)
        try:
            if length >= 5:
                return datetime.time.fromisoformat(value)
        except (ValueError, TypeError):
            raise DataclassCustomError(
                'time_from_rfc3339_parsing',
                '输入应为时间类型，无法解析异常的RFC时间格式'
            )
        raise cls.get_default_error()

    @classmethod
    def get_default_error(cls, msg: optional[str] = None):
        return DataclassCustomError('time_parsing', msg or '输入应为有效时间类型')


class TimedeltaValidator(Validator):
    """时间增量验证器"""

    validator_name = 'timedelta'
    annotation = datetime.timedelta

    def validate(self, value):
        if isinstance_safe(value, self.annotation):
            return value
        elif isinstance_safe(value, (IntegerValidator.annotation, FloatValidator.annotation)):
            return self.annotation(seconds=value)
        maybe_str = StringValidator.maybe_str(value)
        if maybe_str:
            return self.str_to_timedelta(maybe_str)
        raise ValueError("输入应为有效时间增量类型")

    @classmethod
    def str_to_timedelta(cls, value: str):
        # Define regex patterns for both formats
        pattern_1 = re.compile(r'^(-)?(?:(\d+)d,)?(?:(\d+)d)?(\d+):(\d+):(\d+)(?:\.(\d+))?$', re.IGNORECASE)
        pattern_2 = re.compile(r'^([+-])?P?(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?$', re.IGNORECASE)

        # Try matching the first format
        match_1 = pattern_1.match(value)
        if match_1:
            sign, days_1, days_2, hours, minutes, seconds, microseconds = match_1.groups()
            days = int(days_1) if days_1 else (int(days_2) if days_2 else 0)
            hours = int(hours) if hours else 0
            minutes = int(minutes) if minutes else 0
            seconds = int(seconds) if seconds else 0
            microseconds = int(microseconds.ljust(6, '0')) if microseconds else 0

            delta = cls.annotation(days=days, hours=hours, minutes=minutes, seconds=seconds, microseconds=microseconds)
            return -delta if sign else delta

        # Try matching the second format
        match_2 = pattern_2.match(value)
        if match_2:
            sign, days, hours, minutes, seconds = match_2.groups()
            days = int(days) if days else 0
            hours = int(hours) if hours else 0
            minutes = int(minutes) if minutes else 0
            seconds = int(seconds) if seconds else 0

            delta = cls.annotation(days=days, hours=hours, minutes=minutes, seconds=seconds)
            return -delta if sign == '-' else delta
        raise ValueError('输入应为有效时间增量类型')


class DateValidator(Validator):
    """日期验证器"""

    annotation = datetime.date

    def validate(self, value):
        if isinstance_safe(value, self.annotation):
            return value
        elif isinstance_safe(value, DatetimeValidator.annotation):
            return self.datetime_to_date(value)
        try:
            if isinstance_safe(value, (StringValidator.annotation, FloatValidator.annotation,
                                       IntegerValidator.annotation)):
                return DatetimeValidator.str_or_int_to_datetime(value).date()
        except ValueError:
            raise ValueError("输入应为有效日期类型")
        raise ValueError("输入应为有效日期类型")

    @staticmethod
    def datetime_to_date(value: datetime.datetime) -> datetime.date:
        return value.date()


class IntEnumValidator(Validator):
    """整型枚举验证器"""

    validator_name = 'int_enum'
    annotation = enum.IntEnum
    enum_class: enum.EnumType
    values: list

    def __init__(self, enum_class: enum.EnumType, **kwargs):
        super().__init__(**kwargs)
        self.enum_class = enum_class
        self.values = [i.value for i in self.enum_class]

    def validate(self, value):
        if isinstance_safe(value, self.annotation):
            return value
        try:
            return self.enum_class(int(value))
        except (ValueError, TypeError):
            raise DataclassCustomError('int_enum_parsing', f'输入应为 {self.should_input_texts}')

    @property
    def name(self) -> str:
        return f"{self.validator_name}[{_format_type(self.enum_class)}]"

    @property
    def should_input_texts(self) -> str:
        return f'{",".join([f"`{value}`" for value in self.values])}'

    @classmethod
    def build(cls, annotation: _T, **kwargs) -> 'IntEnumValidator':
        if not issubclass_safe(annotation, enum.IntEnum):
            raise DataclassCustomError('building_error', '输入应为IntEnum类型才可构建验证器')
        return cls(annotation, **kwargs)


class EnumValidator(Validator):
    """枚举验证器"""

    validator_name = 'enum'
    annotation = enum.Enum
    enum_class: enum.EnumType
    use_value: bool

    def __init__(self, enum_class: enum.EnumType, use_value: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.enum_class = enum_class
        self.use_value = use_value
        self.values = [i.value if self.use_value else i.name for i in self.enum_class]

    def validate(self, value):
        if isinstance_safe(value, self.enum_class):
            return value
        # 很优的方案，intEnum传递为str时也正确转换
        try:
            if not self.use_value:
                maybe_str = StringValidator.maybe_str(value, raise_error=False)
                return self.enum_class[maybe_str]
            try:
                return self.enum_class(value)
            except ValueError:
                return self.enum_class(int(value))
        except (KeyError, ValueError, TypeError):
            pass
        raise DataclassCustomError('enum_parsing', f'输入应为 {self.should_input_texts}')

    @classmethod
    def build(cls, annotation: _T, **kwargs) -> 'EnumValidator':
        if not issubclass_safe(annotation, enum.Enum):
            raise DataclassCustomError('building_error', '输入应为枚举类型才可构建验证器')
        return cls(annotation, **kwargs)

    @property
    def name(self) -> str:
        return f'{self.validator_name}[{_format_type(self.enum_class)}]'

    @property
    def should_input_texts(self) -> str:
        return f'{",".join([f"`{value}`" for value in self.values])}'


class UuidValidator(Validator):
    """UUID类型验证器"""

    validator_name = 'uuid'
    annotation = uuid.UUID
    version: optional[int]

    def __init__(self, version: optional[int] = None, **kwargs):
        super().__init__(**kwargs)
        self.version: optional[int] = version

    def validate(self, value) -> uuid.UUID:
        try:
            if isinstance_safe(value, self.annotation):
                self.check_version(value, self.version)
                return value
            maybe_str = StringValidator.maybe_str(value, raise_error=False)
            if maybe_str:
                return self.str_to_uuid(maybe_str)
        except DataclassCustomError as e:
            raise e
        except (ValueError, TypeError):
            pass
        raise DataclassCustomError('uuid_parsing', '输入应为有效的UUID')

    @staticmethod
    def check_version(value: uuid.UUID, version: optional[int]):
        if version and value.version != version:
            raise DataclassCustomError('uuid_version', f'输入的UUID值版本错误，应为UUID版本`{version}`')
        return True

    def str_to_uuid(self, value: str) -> uuid.UUID:
        res = uuid.UUID(value)
        self.check_version(res, self.version)
        return res


def matching_validator(annotation: _T, **kwargs):
    """匹配验证器"""
    origin_annotation = type_parser.get_origin_safe(annotation) or annotation
    # Optional原型为Union不放在上面会变成Union验证器
    if type_parser.is_optional(annotation):
        return OptionalValidator.build(annotation, **kwargs)
    try:
        return MATCH_VALIDATOR[origin_annotation].build(annotation, **kwargs)
    except KeyError:
        # 特殊注解
        if issubclass_safe(annotation, enum.IntEnum):
            return MATCH_VALIDATOR[enum.IntEnum].build(annotation, **kwargs)
        elif issubclass_safe(annotation, enum.Enum):
            return MATCH_VALIDATOR[enum.Enum].build(annotation, **kwargs)
        # typing
        elif is_typeddict(annotation):
            return MATCH_VALIDATOR[TypedDict].build(annotation, **kwargs)
        # typing_extensions
        try:
            if typing_extensions.is_typeddict(annotation):
                return MATCH_VALIDATOR[TypedDict].build(annotation, **kwargs)
        except ImportError:
            pass
        return IsInstanceValidator.build(annotation, **kwargs)


def catch_validate_error(
        v,
        val: Validator,
        loc: List[Any],
        errs: List[ErrorDetail],
        exception_type: optional[str] = None,
        errmsg: optional[str] = None
):
    """捕捉异常"""
    try:
        return val.validate(v)
    except ValidationError as e:
        for error in e.errors():
            error.loc.insert(0, *loc)
        errs.extend(e.line_errors)
    except DataclassCustomError as e:
        error = ErrorDetail(
            loc=loc,
            input_value=v,
            exception_type=e.exception_type,
            msg=e.msg,
        )
        errs.append(error)
    except (ValueError, TypeError) as e:
        error = ErrorDetail(
            loc=loc,
            input_value=v,
            exception_type=exception_type or type(e),
            msg=errmsg or str(e),
        )
        errs.append(error)
    except Exception as e:
        error = ErrorDetail(
            loc=loc,
            input_value=v,
            exception_type=exception_type or 'exception_error',
            msg=errmsg or str(e),
        )
        errs.append(error)
    return v


def check_collection_length(annotation, length: int, min_length: int, max_length: int):
    """检查集合长度"""
    annotation_texts = {
        list: '列表',
        tuple: '元祖',
        dict: '字典',
        set: '集合',
        frozenset: '冻结集合',
        Collection: '集合',
        Iterable: '可迭代',
        Generator: '生成器',
        collections.deque: '队列'
    }
    annotation_text = annotation_texts.get(annotation, '集合')
    if min_length is not None and length < min_length:
        raise DataclassCustomError(
            'iter_too_short',
            f'{annotation_text}最小应包含{min_length}项，而不是{length}项'
        )
    elif max_length is not None and length > max_length:
        raise DataclassCustomError(
            'iter_too_long',
            f'{annotation_text}最多应包含{max_length}项，而不是{length}项'
        )


def extract_collection(v, exception_type: str = 'collection_type', type_text: str = '集合'):
    """尝试将其作为一个可迭代可获取长度的东西，但排除字符串和映射类型"""
    if isinstance_safe(v, (list, tuple, set, frozenset)):
        return v
    elif not isinstance_safe(v, (str, bytes, bytearray, dict, Mapping)) and isinstance(v, Collection):
        return v
    raise DataclassCustomError(exception_type, f'输入应为{type_text}类型')


BASE_VALIDATORS = {
    Any: AnyValidator(),
    str: StringValidator(),
    bool: BoolValidator(),
    int: IntegerValidator(),
    float: FloatValidator(),
    bytes: BytesValidator(),
    Decimal: DecimalValidator(),
    datetime.datetime: DatetimeValidator(),
    datetime.date: DateValidator(),
    datetime.time: TimeValidator(),
    datetime.timedelta: TimedeltaValidator(),
    uuid.UUID: UuidValidator(),
}

MATCH_VALIDATOR = {
    Any: AnyValidator,
    str: StringValidator,
    bool: BoolValidator,
    int: IntegerValidator,
    float: FloatValidator,
    bytes: BytesValidator,
    Decimal: DecimalValidator,
    datetime.datetime: DatetimeValidator,
    datetime.date: DateValidator,
    datetime.time: TimeValidator,
    datetime.timedelta: TimedeltaValidator,
    enum.Enum: EnumValidator,
    enum.StrEnum: EnumValidator,
    enum.IntEnum: IntEnumValidator,
    uuid.UUID: UuidValidator,
    Collection: ListValidator,
    collections.abc.Collection: ListValidator,
    Sequence: ListValidator,
    collections.abc.Sequence: ListValidator,
    list: ListValidator,
    List: ListValidator,
    tuple: TupleValidator,
    Tuple: TupleValidator,
    set: SetValidator,
    Set: SetValidator,
    collections.abc.Set: SetValidator,
    frozenset: FrozenValidator,
    FrozenSet: FrozenValidator,
    collections.abc.Mapping: DictValidator,
    dict: DictValidator,
    Dict: DictValidator,
    collections.deque: DequeValidator,
    Deque: DequeValidator,
    Literal: LiteralValidator,
    Optional: OptionalValidator,
    Union: UnionValidator,
    Iterable: GeneratorValidator,
    collections.abc.Iterable: GeneratorValidator,
    Generator: GeneratorValidator,
    collections.abc.Generator: GeneratorValidator,
    Type: IsSubClassValidator,
    type: IsSubClassValidator,
    TypedDict: TypedDictValidator,
}