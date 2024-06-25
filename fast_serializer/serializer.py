# -*- coding:utf-8 -*-
import enum
from typing import Type, Dict, Any, Union, Tuple
from .constants import _T, _DATACLASS_FIELDS_NAME, _POST_INIT_NAME
from .exceptions import ErrorDetail, ValidationError
from .field import Field
from .type_parser import type_parser
from .utils import _format_type
from .validator import Validator, EnumValidator, TupleValidator
from .exceptions import DataclassCustomError


class FastSerializer:
    """序列化器提供强大的序列化和反序列化"""

    catch_val_exceptions: Tuple[Type[Exception]] = (ValueError, TypeError, RuntimeError, DataclassCustomError)

    def __init__(self):
        self.field_validators: Dict[str, Validator] = {}  # 自定义的字段验证器
        # self.type_validators: Dict[Any, Validator] = {}  # 用户编写的自定义类型验证器

    def deserialize(self, data: Union[dict, object], target=None, instance=None) -> _T:
        """反序列化 Deserialize"""
        # if target is None and instance is None:
        #     raise RuntimeError('目标类和实例不能同时为空')

        if target is None:
            target = instance.__class__
        class_name: str = target.__name__
        dataclass_fields: Dict[str, Field] = getattr(target, _DATACLASS_FIELDS_NAME, {})
        errors = []
        for field_name, field in dataclass_fields.items():
            input_value = self._get_value(data, True, field_name, field)
            try:
                """数据为必填项"""
                if input_value is None and field.required:
                    raise DataclassCustomError('missing', f"{field_name} 为必填项")
                elif input_value is not None:
                    input_value = field.validator.validate(input_value)

                setattr(instance, field_name, input_value)
            except ValidationError as e:
                for error in e.line_errors:
                    error.loc.insert(0, field_name)
                errors.extend(e.line_errors)
            except self.catch_val_exceptions as e:
                # raise e
                if type(e) is DataclassCustomError:
                    error_detail = ErrorDetail(
                        # key=field_name,
                        loc=[field_name],
                        input_value=input_value,
                        exception_type=e.exception_type,
                        msg=e.msg
                    )
                else:
                    error_detail = ErrorDetail(
                        # key=field_name,
                        loc=[field_name],
                        input_value=input_value,
                        exception_type=e,
                        msg=str(e)
                    )
                errors.append(error_detail)

        if errors:
            raise ValidationError(title=class_name, line_errors=errors)

        # post_init
        if hasattr(instance, _POST_INIT_NAME):
            getattr(instance, _POST_INIT_NAME)()

        return instance  # type: ignore

    @staticmethod
    def _get_value(data: Union[dict, object], is_dict: bool, field_name: str, field: Field) -> Any:
        try:
            value = data.__getitem__(field_name) if is_dict else getattr(data, field_name)
        except (KeyError, AttributeError):
            value = field.get_default_value()
        return value