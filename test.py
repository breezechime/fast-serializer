import pydantic_core.core_schema
from pydantic import BaseModel

from fast_serializer.validator import FunctionValidator


# 没有参数
def test1():
    """
    arguments_validator: Arguments(
                                    ArgumentsValidator {
                                        parameters: [],
                                        positional_params_count: 0,
                                        var_args_validator: None,
                                        var_kwargs_validator: None,
                                        loc_by_alias: true,
                                        extra: Forbid,
                                    },
                                ),
    """
    pass


# 有一个POSITIONAL_OR_KEYWORD
def test2(x: int):
    """
    arguments_validator: Arguments(
                                    ArgumentsValidator {
                                        parameters: [
                                            Parameter {
                                                positional: true,
                                                name: "x",
                                                kw_lookup_key: Some(
                                                    Simple {
                                                        key: "x",
                                                        py_key: Py(
                                                            0x0000000100d96d50,
                                                        ),
                                                        path: LookupPath(
                                                            [
                                                                S(
                                                                    "x",
                                                                    Py(
                                                                        0x0000000100d96d50,
                                                                    ),
                                                                ),
                                                            ],
                                                        ),
                                                    },
                                                ),
                                                kwarg_key: Some(
                                                    Py(
                                                        0x0000000100d21198,
                                                    ),
                                                ),
                                                validator: Int(
                                                    IntValidator {
                                                        strict: false,
                                                    },
                                                ),
                                            },
                                        ],
                                        positional_params_count: 1,
                                        var_args_validator: None,
                                        var_kwargs_validator: None,
                                        loc_by_alias: true,
                                        extra: Forbid,
                                    },
                                ),
    """
    pass


# 有一个POSITIONAL_ONLY
def test3(x: int, /):
    """
    arguments_validator: Arguments(
                                    ArgumentsValidator {
                                        parameters: [
                                            Parameter {
                                                positional: true,
                                                name: "x",
                                                kw_lookup_key: None,
                                                kwarg_key: None,
                                                validator: Int(
                                                    IntValidator {
                                                        strict: false,
                                                    },
                                                ),
                                            },
                                        ],
                                        positional_params_count: 1,
                                        var_args_validator: None,
                                        var_kwargs_validator: None,
                                        loc_by_alias: true,
                                        extra: Forbid,
                                    },
                                ),
    """
    pass


# 有一个VAR_POSITIONAL
def test4(*args: tuple[str, ...]):
    """
    arguments_validator: Arguments(
                                    ArgumentsValidator {
                                        parameters: [],
                                        positional_params_count: 0,
                                        var_args_validator: Some(
                                            Tuple(
                                                TupleValidator {
                                                    strict: false,
                                                    validators: [
                                                        Str(
                                                            StrValidator {
                                                                strict: false,
                                                                coerce_numbers_to_str: false,
                                                            },
                                                        ),
                                                    ],
                                                    variadic_item_index: Some(
                                                        0,
                                                    ),
                                                    min_length: None,
                                                    max_length: None,
                                                    name: "tuple[str, ...]",
                                                },
                                            ),
                                        ),
                                        var_kwargs_validator: None,
                                        loc_by_alias: true,
                                        extra: Forbid,
                                    },
                                ),
    """
    pass


# 有一个KEYWORD_ONLY
def test5(*args, x: int):
    """
    arguments_validator: Arguments(
                                    ArgumentsValidator {
                                        parameters: [
                                            Parameter {
                                                positional: false,
                                                name: "x",
                                                kw_lookup_key: Some(
                                                    Simple {
                                                        key: "x",
                                                        py_key: Py(
                                                            0x0000000102b3ed50,
                                                        ),
                                                        path: LookupPath(
                                                            [
                                                                S(
                                                                    "x",
                                                                    Py(
                                                                        0x0000000102b3ed50,
                                                                    ),
                                                                ),
                                                            ],
                                                        ),
                                                    },
                                                ),
                                                kwarg_key: Some(
                                                    Py(
                                                        0x0000000102ac9198,
                                                    ),
                                                ),
                                                validator: Int(
                                                    IntValidator {
                                                        strict: false,
                                                    },
                                                ),
                                            },
                                        ],
                                        positional_params_count: 0,
                                        var_args_validator: Some(
                                            Any(
                                                AnyValidator,
                                            ),
                                        ),
                                        var_kwargs_validator: None,
                                        loc_by_alias: true,
                                        extra: Forbid,
                                    },
                                ),
    """
    pass


# 有一个VAR_KEYWORD
def test6(**kwargs):
    """
     arguments_validator: Arguments(
                                    ArgumentsValidator {
                                        parameters: [],
                                        positional_params_count: 0,
                                        var_args_validator: None,
                                        var_kwargs_validator: Some(
                                            Any(
                                                AnyValidator,
                                            ),
                                        ),
                                        loc_by_alias: true,
                                        extra: Forbid,
                                    },
                                ),
    """
    pass


# 组合
def test7(x: int, /, **kwargs):
    """
    arguments_validator: Arguments(
                                    ArgumentsValidator {
                                        parameters: [
                                            Parameter {
                                                positional: true,
                                                name: "x",
                                                kw_lookup_key: None,
                                                kwarg_key: None,
                                                validator: Int(
                                                    IntValidator {
                                                        strict: false,
                                                    },
                                                ),
                                            },
                                        ],
                                        positional_params_count: 1,
                                        var_args_validator: None,
                                        var_kwargs_validator: Some(
                                            Any(
                                                AnyValidator,
                                            ),
                                        ),
                                        loc_by_alias: true,
                                        extra: Forbid,
                                    },
                                ),
    """
    pass


class TestModel(BaseModel):
    call: test7


# pydantic_core.core_schema.call_schema()
# pydantic_core.core_schema.arguments_schema()
# print(TestModel.__pydantic_validator__)
val = FunctionValidator.build(test1)
print(val)