# -*- coding:utf-8 -*-
import json
from typing import (
    Any, List, Union
)
from .types import optional
from .utils import camel_to_snake, _format_type, isinstance_safe


def _format_exception_type(exception_type: Union[str, type]) -> str:
    if isinstance_safe(exception_type, str):
        return exception_type
    return camel_to_snake(exception_type.__class__.__name__)


class ErrorDetail:
    """错误详情"""

    """键名"""
    # key: str

    """键名索引列表"""
    loc: List[Any]

    """输入值"""
    input_value: Any

    """异常类型"""
    exception_type: str

    """错误信息"""
    msg: str

    """上下文信息"""
    ctx: optional[dict[str, Any]]

    __slots__ = ('loc', 'input_value', 'exception_type', 'msg', 'ctx')

    def __init__(self, loc: List[Any], input_value: Any, exception_type: Union[str, type], msg: str,
                 ctx: optional[dict[str, Any]] = None):
        # self.key = key
        self.loc = loc
        self.input_value = input_value
        self.exception_type = _format_exception_type(exception_type)
        self.msg = msg
        self.ctx = ctx

    def __str__(self):
        return json.dumps(self.__dict__(), indent=4, ensure_ascii=False)

    def __repr__(self):
        return self.__str__()

    def __dict__(self):
        return {
            # 'key': self.key,
            'loc': self.loc,
            'input_value': self.input_value,
            'exception_type': self.exception_type,
            'msg': self.msg,
            'ctx': self.ctx
        }


class ValidationError(ValueError):
    title: str
    line_errors: List[ErrorDetail]

    def __init__(self, title: str, line_errors: List[ErrorDetail], *args):
        super().__init__(*args)
        self.title = title
        self.line_errors = line_errors or []

    def errors(self):
        return self.line_errors

    def error_count(self) -> int:
        return len(self.line_errors)

    def json(self) -> str:
        return json.dumps(self.__dict__(), indent=4, ensure_ascii=False)

    def __str__(self):
        plural = 's' if len(self.line_errors) > 1 else ''
        return f'{len(self.line_errors)} validation error{plural} for {self.title}\n{self.format_line_errors()}'

    def __repr__(self):
        return self.__str__()

    def __dict__(self):
        return [error.__dict__() for error in self.line_errors]

    def format_line_errors(self):
        text = ""
        length = len(self.line_errors)
        for index, error in enumerate(self.line_errors):
            enter_line = '' if index == length - 1 else '\n'
            end_text = (f"["
                        f"exception_type={error.exception_type}, "
                        f"input_value={error.input_value!r}, "
                        f"input_type={_format_type(error.input_value)}"
                        f"]")
            text += f"{'.'.join([str(e) for e in error.loc])}\n  {error.msg} {end_text}{enter_line}"
        return text


class DataclassCustomError(ValueError):
    exception_type: str
    msg: str
    context: optional[dict]

    def __init__(self, exception_type: str, msg: str, context: optional[dict] = None, *args):
        super().__init__(*args)
        self.exception_type = exception_type
        self.msg = msg
        self.context = context

    def message(self):
        return self.format_message(self.msg, self.context)

    def __str__(self):
        return self.message()

    def __repr__(self):
        msg = self.message()
        if self.context is not None:
            context_repr = {k: repr(v) for k, v in self.context.items()}
            return f"{msg} [type={self.error_type}, context={context_repr}]"
        else:
            return f"{msg} [type={self.error_type}, context=None]"

    @staticmethod
    def format_message(msg: str, context: optional[str]) -> str:
        if not context:
            return msg
        message = msg
        for key, value in context.items():
            placeholder = f"{{{key}}}"
            if isinstance(value, str):
                message = message.replace(placeholder, value)
            elif isinstance(value, int):
                message = message.replace(placeholder, str(value))
            else:
                # fallback for anything else just in case
                message = message.replace(placeholder, str(value))
        return message


class ValidatorBuildingError(TypeError):

    def __init__(self, msg: str, *args):
        super().__init__(*args)
        self.msg = msg

    def __str__(self):
        return self.msg

    def __repr__(self):
        return self.__str__()