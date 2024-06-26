import time
from typing import Callable

from fast_serializer import FastDataclass
from fast_serializer.validator import FunctionValidator, CallableValidator


class Test(FastDataclass):

    arr: list[int]


def test(v: str):
    print(v)


# print(Test.)
# val = FunctionValidator.build(test)
# val.validate(())
# val = CallableValidator.build(Callable)
# print(val)
# print(arr)