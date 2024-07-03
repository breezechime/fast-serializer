import collections
import enum
import time
import typing
import typing_extensions
import uuid
from typing import Callable, Union
from fast_serializer import FastDataclass, field
from fast_serializer.validator import FunctionValidator, CallableValidator, TupleValidator, TypedDictValidator
from typing_extensions import TypedDict, is_typeddict


class AType(enum.IntEnum):
    RED = 1

    BLUE = 2


class HaHa(TypedDict, total=False):
    name: int


class Test(FastDataclass):

    arr: HaHa


def test(v: str, *args):
    print(v)


val = FunctionValidator.build(test)
print(val.validate([1]))
# print(HaHa())
# TypedDictValidator.build(HaHa)
# print(Union[str])
# print(dir(HaHa))
# print(is_typeddict(HaHa))
# print(Test.dataclass_fields['arr'])
# a = Test(arr={'name': 'asd'})
# print(a.arr)
# print(next(a.arr))
# print(type(a.arr))
# val = TupleValidator.build(tuple[str, int])
# v = val.validate((1,))
# print(v)
# a = set()
# a.add(1)
# a.add(1)
# print(a)
# print(Test.dataclass_fields)
# print(Test.)
# val = FunctionValidator.build(test)
# val.validate(())
# val = CallableValidator.build(Callable)
# print(val)
# print(arr)