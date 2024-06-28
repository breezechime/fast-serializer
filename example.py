import enum
import time
import typing
from typing import Callable, Union
from fast_serializer import FastDataclass, field
from fast_serializer.validator import FunctionValidator, CallableValidator, TupleValidator


class Type(enum.IntEnum):
    RED = 1

    BLUE = 2


class Test(FastDataclass):

    arr: typing.Sequence[str]


def test(v: str):
    print(v)


# print(Union[str])
# print(Test.dataclass_fields['arr'].validator)
a = Test(arr=(1,))
print(a.arr)
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