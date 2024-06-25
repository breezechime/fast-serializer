# -*- coding:utf-8 -*-
import collections
import datetime
import decimal
import enum
import inspect
import re
import time
import uuid
from abc import ABC, abstractmethod
from decimal import Decimal
from types import FunctionType
from typing import (
    Any, Deque, Generator, Union, Collection, Iterable, Literal, NoReturn, List, get_args, Tuple, Set, Dict, Optional,
    Sequence, Mapping, Callable
)

from .constants import _T
from .exceptions import DataclassCustomError, ErrorDetail, ValidationError
from .type_parser import type_parser
from .types import optional
from .utils import _format_type, get_sub_validator_kwargs, isinstance_safe, issubclass_safe


class Validator(ABC):
    """验证器基类"""

    name: str
    annotation: _T

    def __init__(self, **kwargs): ...

    @abstractmethod
    def validate(self, value, **kwargs): ...

    def is_instance(self, value, annotation=None) -> bool:
        annotation = annotation or self.annotation
        return isinstance_safe(value, annotation)

    def get_name(self) -> str:
        return self.name

    def update_validator(self) -> None: ...

    def __repr__(self):
        return f"{self.__class__.__name__}(\n\tname: {self.name!r},\n\tannotation: {self.annotation}\n)"

    @classmethod
    def build(cls, annotation: _T, **kwargs) -> 'Validator':
        return cls(**kwargs)


class AnyValidator(Validator):
    """任意类型验证器"""

    name = 'any'
    annotation = Any

    def validate(self, value, **kwargs):
        return value


class StringValidator(Validator):
    """字符串验证器"""

    name = 'str'
    annotation = str
    allow_number: bool = True

    def __init__(self, allow_number: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.allow_number = allow_number

    def validate(self, value, allow_number: bool = None, **kwargs) -> str:
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

    name = 'bool'
    annotation = bool

    def validate(self, value, **kwargs) -> bool:
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

    name = 'int'
    annotation = int
    half_adjust_value = 0.11

    def validate(self, value, **kwargs):
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

    name = 'float'
    annotation = float

    def validate(self, value, **kwargs):
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

    name = 'decimal'
    annotation = Decimal

    def validate(self, value, **kwargs):
        if self.is_instance(value, self.annotation):
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

    name = 'bytes'
    annotation = bytes

    def validate(self, value, **kwargs):
        if isinstance_safe(value, self.annotation):
            return value
        elif isinstance_safe(value, StringValidator.annotation):
            return value.encode('utf-8')
        elif isinstance_safe(value, bytearray):
            return self.annotation(value)
        raise ValueError('输入应为有效字节类型')


class TargetTypeValidator(Validator):
    """目标类型验证器"""

    name = 'target_type'

    def __init__(self, annotation: _T, **kwargs):
        super().__init__(**kwargs)
        self.annotation = annotation
        self.name = _format_type(annotation)

    def validate(self, value, **kwargs):
        if isinstance_safe(value, self.annotation):
            return value
        raise ValueError(f'输入应为`{self.name}`类型')

    @classmethod
    def build(cls, annotation: _T, **kwargs) -> 'Validator':
        return cls(annotation, **kwargs)


class OptionalValidator(Validator):
    """可空类型验证器"""

    name = 'optional'
    annotation = optional
    validator: Validator

    def __init__(self, validator: Validator, **kwargs):
        super().__init__(**kwargs)
        self.validator = validator
        self.update_validator()

    def validate(self, value, **kwargs):
        if value is None:
            return value
        return self.validator.validate(value)

    @classmethod
    def build(cls, annotation: _T, **kwargs):
        if not type_parser.is_optional(annotation):
            annotation = Optional[annotation]
        validator = matching_validator(get_args(annotation)[0], **kwargs)
        return cls(validator=validator, **kwargs)

    def update_validator(self) -> None:
        self.name = f"optional[{self.validator.name}]"


class UnionValidator(Validator):
    """联合类型验证器"""

    name = 'union'
    annotation = Union
    validators: List[Validator]

    def validate(self, value, **kwargs):
        error = None
        for validator in self.validators:
            try:
                return validator.validate(value)
            except (Exception,) as e:
                error = e
                continue
        raise error

    @classmethod
    def build(cls, annotation: _T, **kwargs):
        raise NotImplementedError('asd')
        # if not type_parser.is_union(annotation):
        #     raise ValueError(f"输入应为Union注解才可构建 {cls.__name__}")
        # validator = cls()
        # validator.validators = [matching_validator(ann) for ann in get_args(annotation)]
        # return validator


class LiteralValidator(Validator):
    """字面量类型验证器"""

    name = 'literal'
    annotation = Literal
    expected_values: Tuple[Any, ...]

    def __init__(self, *expected: Tuple[Any, ...], **kwargs):
        super().__init__(**kwargs)
        self.expected_values = expected
        self.update_validator()

    def validate(self, value, **kwargs):
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
                f"\n\tname: {self.name}"
                f"\n\tannotation: {self.annotation}"
                f"\n\tvalues: {self.expected_values}\n"
                f")")

    def update_validator(self):
        self.name = f'literal[{",".join([f"{value!r}" for value in self.expected_values])}]'

    @property
    def format_expected_values(self):
        return f'{", ".join([f"`{value!r}`" for value in self.expected_values])}'


# TODO
class FastDataclassValidator(Validator):
    """快速数据类验证器"""

    def validate(self, value, **kwargs):
        pass


class PydanticModelValidator(Validator):
    """Pydantic模型验证器"""

    def validate(self, value, **kwargs):
        try:
            from pydantic import BaseModel
        except ImportError:
            raise ImportError('导入Pydantic失败, 可能未安装')
        if issubclass_safe(value, BaseModel):
            return value
        raise ValueError('输入应为Pydantic模型')


class DataclassValidator(Validator):
    """数据类验证器"""

    name = 'dataclass'

    def validate(self, value, **kwargs):
        try:
            from dataclasses import is_dataclass
        except ImportError:
            raise ImportError('导入Dataclass失败, 您把它删了吗？')
        if is_dataclass(value):
            return value
        raise ValueError('输入应为Dataclass数据类')


class DictValidator(Validator):
    """字典验证器"""

    name = 'dict'
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
        self.update_validator()

    def validate(self, value, **kwargs):
        if not isinstance_safe(value, Mapping):
            raise DataclassCustomError('dict_type', '输入应为有效键值对')
        # 验证长度
        length = len(value)
        IterableValidator.check_length(self.annotation, length, self.min_length, self.max_length)
        # 优化（双any可省略很多验证性能）
        key_validator_is_any = self.key_validator.annotation is Any
        value_validator_is_any = self.value_validator.annotation is Any
        if key_validator_is_any and value_validator_is_any:
            return value
        # 验证keys(any优化)
        if key_validator_is_any:
            keys: list = value.keys()
        else:
            keys: list = []
            IterableValidator.validate_iter(self.name, self.key_validator, value.keys(), keys)
        # 验证values
        if value_validator_is_any:
            values: list = value.values()
        else:
            values: list = []
            IterableValidator.validate_iter(self.name, self.value_validator, value.values(), values)
        res_dict = self.annotation(zip(keys, values))
        return res_dict

    @classmethod
    def build(cls, annotation: _T, **kwargs) -> 'DictValidator':
        _args = get_args(annotation)
        _args_length = len(_args)
        key_validator = matching_validator(_args[0], **kwargs) if _args_length >= 1 else BASE_VALIDATORS[Any]
        value_validator = matching_validator(_args[1], **kwargs) if _args_length >= 2 else BASE_VALIDATORS[Any]
        return cls(key_validator, value_validator, *_args, **kwargs)

    def update_validator(self) -> None:
        self.name = f'dict[{self.key_validator.name}, {self.value_validator.name}]'


class TypedDictField:
    name: str
    required: bool


# TODO
class TypedDictValidator(Validator):
    """带类型字典验证器"""

    def validate(self, value, **kwargs):
        pass


class IterableValidator(Validator):
    """可迭代验证器"""

    name = 'iterable'
    annotation = Iterable
    item_validator: Validator
    min_length: optional[int]
    max_length: optional[int]

    def __init__(self, item_validator: Validator, min_length: optional[int] = None, max_length: optional[int] = None,
                 **kwargs):
        super().__init__(**kwargs)
        self.item_validator = item_validator
        self.min_length = min_length
        self.max_length = max_length
        self.update_validator()

    def validate(self, value, **kwargs):
        is_iterable = isinstance_safe(value, Iterable)
        if not is_iterable:
            raise DataclassCustomError('iterable_type', f'输入应为可迭代类型')
        # 验证长度
        IterableValidator.check_length(self.annotation, len(value), self.min_length, self.max_length)
        results = []
        IterableValidator.validate_iter(self.name, self.item_validator, value, results)
        return results

    @staticmethod
    def validate_iter(name: str, item_validator: Validator, value, results):
        errors: List[ErrorDetail] = []
        # 验证子元素
        for index, item in enumerate(value):
            try:
                results.append(item_validator.validate(item))
            except ValidationError as e:
                for error in e.errors():
                    error.loc.insert(0, index)
                errors.extend(e.line_errors)
            except DataclassCustomError as e:
                error = ErrorDetail(
                    # key=str(index),
                    loc=[index],
                    input_value=item,
                    exception_type=e.exception_type,
                    msg=e.msg,
                )
                errors.append(error)
            except (ValueError, TypeError) as e:
                error = ErrorDetail(
                    # key=str(index),
                    loc=[index],
                    input_value=item,
                    exception_type=type(e),
                    msg=str(e),
                )
                errors.append(error)
        if errors:
            raise ValidationError(title=name, line_errors=errors)

    @classmethod
    def extract_iterable(cls, value: Iterable, exception_type: str = 'iter_type', type_text: str = '可迭代'):
        # 尝试将其作为一个可生成可迭代的东西，但排除字符串和映射类型
        if isinstance_safe(value, (list, tuple, set, frozenset)):
            return value
        elif not isinstance_safe(value, (str, bytes, bytearray, dict, Mapping)) and isinstance(value, Collection):
            return value
        raise DataclassCustomError(exception_type, f'输入应为{type_text}类型')

    @staticmethod
    def check_length(annotation, length: int, min_length: int, max_length: int):
        annotation_texts = {
            list: '列表',
            tuple: '元祖',
            dict: '字典',
            set: '集合',
            frozenset: '冻结集合',
            Collection: '集合'
        }
        annotation_text = annotation_texts.get(annotation, '可迭代类型')
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

    @classmethod
    def build(cls, annotation: _T, **kwargs) -> 'IterableValidator':
        _args = get_args(annotation)
        sub_annotation = _args[0] if _args else Any
        item_validator = matching_validator(sub_annotation, **get_sub_validator_kwargs(kwargs))
        return cls(item_validator=item_validator, **kwargs)

    def update_validator(self) -> None:
        self.name = f'iterable[{self.item_validator.name}]'


class ListValidator(Validator):
    """列表验证器"""

    name = 'list'
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
        self.update_validator()

    def validate(self, value, **kwargs):
        value = extract_iterable(value, 'list_type', '列表')
        # 验证长度
        IterableValidator.check_length(self.annotation, len(value), self.min_length, self.max_length)
        # 优化
        if self.item_validator.annotation is Any:
            return self.annotation(value) if not isinstance_safe(value, self.annotation) else value
        results: list = []
        # 验证
        IterableValidator.validate_iter(self.name, self.item_validator, value, results)
        return results

    def __repr__(self):
        return (f"{self.__class__.__name__}(\n\t"
                f"name: {self.name},\n\t"
                f"annotation: {self.annotation}\n\t"
                f"item_validator: {self.item_validator},\n\t"
                f"\n)")

    @classmethod
    def build(cls, annotation: _T, **kwargs) -> 'ListValidator':
        args = get_args(annotation)
        sub_annotation = args[0] if args else Any
        item_validator = matching_validator(sub_annotation, **get_sub_validator_kwargs(kwargs))
        return cls(item_validator=item_validator, **kwargs)

    def update_validator(self) -> None:
        self.name = f'list[{self.item_validator.name}]'


class TupleValidator(Validator):
    """元组验证器"""

    name = 'tuple'
    annotation = tuple
    item_validator: Validator
    min_length: optional[int]
    max_length: optional[int]

    def __init__(self, item_validator: Validator, min_length: optional[int] = None, max_length: optional[int] = None,
                 **kwargs):
        super().__init__(**kwargs)
        self.item_validator = item_validator
        self.min_length = min_length
        self.max_length = max_length
        self.update_validator()

    def validate(self, value, **kwargs):
        is_iterable = isinstance_safe(value, Iterable)
        if not is_iterable:
            raise DataclassCustomError('tuple_type', f'输入应为元组类型')
        # 验证长度
        IterableValidator.check_length(self.annotation, len(value), self.min_length, self.max_length)
        results = []
        IterableValidator.validate_iter(self.name, self.item_validator, value, results)
        return results

    @classmethod
    def build(cls, annotation: _T, **kwargs) -> 'TupleValidator':
        _args = get_args(annotation)
        sub_annotation = _args[0] if _args else Any
        item_validator = matching_validator(sub_annotation, **get_sub_validator_kwargs(kwargs))
        return cls(item_validator=item_validator, **kwargs)

    def update_validator(self) -> None:
        self.name = f'list[{self.item_validator.name}]'


# TODO
class SetValidator(Validator):
    """集合验证器"""

    name = 'set'
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

    def validate(self, value, **kwargs):
        pass

    @classmethod
    def build(cls, annotation: _T, **kwargs) -> 'SetValidator':
        if type_parser.is_iterable(annotation):
            raise ValueError(f"输入应为可迭代类型注解才可构建 {cls.__name__}")
        return cls()


# TODO
class FrozenValidator(Validator):
    """冻结集合验证器"""

    name = 'frozenset'
    annotation = frozenset

    def validate(self, value, **kwargs):
        self.item_validator: Validator


# TODO
class GeneratorValidator(Validator):
    """生成器验证器"""

    name = 'generator'
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

    def validate(self, value, **kwargs):
        is_iterable = isinstance_safe(value, Iterable)
        if not is_iterable:
            raise DataclassCustomError('iterable_type', '输入应为可迭代类型')
        return value

    @classmethod
    def build(cls, annotation: _T, **kwargs) -> 'GeneratorValidator':
        args = get_args(annotation)
        sub_annotation = args[0] if args else Any
        item_validator = matching_validator(sub_annotation, **get_sub_validator_kwargs(kwargs))
        return cls(item_validator=item_validator, **kwargs)


# TODO
class FunctionValidator(Validator):
    """函数验证器，传递函数参数自动调用函数"""

    name = 'function'
    annotation = FunctionType
    """参数验证器列表"""
    argument_validators: List[Validator]

    def __init__(self, argument_validators: List[Validator], function: FunctionType, **kwargs):
        super().__init__(**kwargs)
        self.argument_validators = argument_validators
        self.function = function

    def validate(self, value, **kwargs):
        is_list = isinstance_safe(value, ListValidator.annotation)
        is_tuple = isinstance_safe(value, TupleValidator.annotation)
        is_dict = isinstance_safe(value, DictValidator.annotation)
        if not is_list and not is_tuple and not is_dict:
            raise DataclassCustomError('arguments_type', '参数必须是元组、列表或字典')
        parameters = inspect.signature(self.function).parameters
        # if is_list or is_tuple:
        # return

    @classmethod
    def build(cls, annotation: _T, **kwargs) -> 'FunctionValidator':
        is_function = type_parser.is_function(annotation)
        if not is_function:
            raise DataclassCustomError('func_building', '输入应为函数才可构建函数验证器')
        parameters = inspect.signature(annotation).parameters
        function_annos = []
        for k, param in parameters.items():
            # 排除 *args, **kwargs，并且将可以不传的参数组合成OptionalValidator
            if param.kind in [inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD]:
                continue
            param_anno = param.annotation if param.default == inspect.Parameter.empty \
                else Optional[param.annotation]
            function_annos.append(param_anno)

        argument_validators = [matching_validator(anno, **get_sub_validator_kwargs(kwargs, i))
                               for i, anno in enumerate(function_annos)]
        return cls(argument_validators=argument_validators, function=annotation, **kwargs)


# TODO
class CallableValidator(Validator):
    name = 'callable'
    annotation = Callable

    """指定函数"""
    function: optional[FunctionType]

    def __init__(self, function_or_callable: Union[FunctionType, Callable], **kwargs):
        super().__init__(**kwargs)
        is_function = type_parser.is_function(function_or_callable)
        if not is_function and not isinstance_safe(function_or_callable, Callable):
            raise DataclassCustomError('callable_building', '输入应为可调用类型才可构建Callable验证器')
        if is_function:
            self.function = function_or_callable
        else:
            self.annotation = function_or_callable
        self.update_validator()

    def validate(self, value, **kwargs):
        pass

    @classmethod
    def build(cls, annotation: _T, **kwargs) -> 'CallableValidator':
        return cls(function_or_callable=annotation, **kwargs)

    def update_validator(self) -> None:
        pass


class DatetimeValidator(Validator):
    """日期时间验证器"""

    name = 'datetime'
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

    def validate(self, value, **kwargs):
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

    name = 'time'
    annotation = datetime.time
    """模式：second模式数字当秒处理，time模式数字将转换时间，默认`second`"""
    mode: Literal['second', 'time']

    def __init__(self, mode: Literal['second', 'time'] = 'second', **kwargs):
        super().__init__(**kwargs)
        self.mode = mode

    def validate(self, value, **kwargs):
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

    name = 'timedelta'
    annotation = datetime.timedelta

    def validate(self, value, **kwargs):
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

    def validate(self, value, **kwargs):
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


class EnumValidator(Validator):
    """枚举验证器"""

    name = 'enum'
    annotation = enum.Enum

    def __init__(self, target_enum: optional[enum.Enum] = None, use_value: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.target_enum: optional[enum.Enum] = target_enum
        self.use_value = use_value
        self.names = []
        self.values = []
        self.update_validator()

    def validate(self, value, **kwargs):
        try:
            if self.target_enum is None and issubclass_safe(value, self.annotation):
                return value
            elif self.target_enum and isinstance_safe(value, self.target_enum):
                return value
            elif self.target_enum and isinstance_safe(value, IntegerValidator.annotation):
                return self.int_to_enum(value)
            maybe_str = StringValidator.maybe_str(value, raise_error=False)
            if self.target_enum and maybe_str:
                return self.str_to_enum(maybe_str)
        except (Exception,):
            self.raise_error()
        self.raise_error()

    def update_validator(self):
        self.name = f'enum[{str(self.target_enum)}]' if self.target_enum is not None else 'enum'
        if self.target_enum:
            for item in self.target_enum:
                self.names.append(item.name)
                self.values.append(item.value)

    def int_to_enum(self, value: int):
        return self.target_enum(value)

    def str_to_enum(self, value: str):
        if self.use_value:
            return self.target_enum(value)
        return self.target_enum[value]

    @property
    def exact_values(self):
        return self.values if self.use_value else self.names

    @property
    def exact_text(self):
        return f'{",".join([f"`{value}`" for value in self.exact_values])}'

    def raise_error(self) -> NoReturn:
        if self.target_enum:
            raise ValueError(f'输入应为 {self.exact_text}')
        else:
            raise ValueError('输入应为枚举类型')


class DequeValidator(Validator):
    """队列验证器"""

    name = 'deque'
    annotation = collections.deque
    item_validator: Validator

    def __init__(self, item_validator: optional[Validator] = None, **kwargs):
        super().__init__(**kwargs)
        self.item_validator = item_validator or BASE_VALIDATORS[Any]
        self.update_validator()

    def validate(self, value, **kwargs) -> collections.deque:
        if not type_parser.is_collection(value):
            raise ValueError('输入应为可迭代类型')
        new_deque = self.annotation()
        # 开始验证内部
        [new_deque.append(self.item_validator.validate(item)) for item in value]
        return new_deque

    @classmethod
    def build(cls, annotation: _T, **kwargs) -> 'DequeValidator':
        if not type_parser.is_collection(annotation):
            raise ValueError(f"输入应为集合类型注解才可构建 {cls.__name__}")
        args = get_args(annotation)
        item_validator = matching_validator(args[0]) if args else None
        validator = cls(item_validator)
        return validator

    def __repr__(self):
        return (f"{self.__class__.__name__}(\n\tname: {self.name},\n\tannotation: "
                f"{self.annotation},\n\titem_validator: {self.item_validator}\n)")

    def update_validator(self):
        self.name = f'deque[{self.item_validator.name}]'


class UuidValidator(Validator):
    """UUID类型验证器"""

    name = 'uuid'
    annotation = uuid.UUID

    def __init__(self, version: optional[int] = None, **kwargs):
        super().__init__(**kwargs)
        self.version: optional[int] = version

    def validate(self, value, **kwargs) -> uuid.UUID:
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
    # 特殊注解
    if getattr(annotation, '_name', None) == 'Optional':
        return OptionalValidator.build(annotation, **kwargs)
    try:
        return MATCH_VALIDATOR[origin_annotation].build(annotation, **kwargs)
    except KeyError:
        return TargetTypeValidator.build(annotation, **kwargs)


def extract_iterable(v, exception_type: str = 'collection_type', type_text: str = '集合'):
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
    enum.Enum: EnumValidator(),
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
    uuid.UUID: UuidValidator,
    Iterable: IterableValidator,
    Collection: ListValidator,
    Sequence: ListValidator,
    list: ListValidator,
    List: ListValidator,
    tuple: TupleValidator,
    Tuple: TupleValidator,
    set: SetValidator,
    Set: SetValidator,
    frozenset: FrozenValidator,
    dict: DictValidator,
    Dict: DictValidator,
    collections.deque: DequeValidator,
    Deque: DequeValidator,
    Literal: LiteralValidator,
    Optional: OptionalValidator,
    # NoneType: OptionalValidator,
    Union: UnionValidator,
    Generator: GeneratorValidator,
}
