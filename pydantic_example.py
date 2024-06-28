import enum
import time
from typing import Callable, Union, Generator, NamedTuple, Sequence, Type

from pydantic import BaseModel, TypeAdapter, InstanceOf
from pydantic_core import core_schema


def test(*args: str, a: str, **kwargs):
    pass
    # print(args)
    # print(kwargs)


class Point(NamedTuple):
    x: int
    y: int


class AType(enum.StrEnum):
    RED = 'a'


class Test(BaseModel):

    arr: Type[Point]


# print(type((i for i in range(10))))
print(Test.__pydantic_validator__)
# print(type(Type))
# print(Test.__pydantic_validator__)
test = Test(arr=('asd',))
print(test.arr)
# val = core_schema.arguments_schema()
# print(val)
# print(val)
# print(Test.__pydantic_validator__)
# print(Test(arr=(1, 2)))
# now = time.time()
# arr = []
# for i in range(100000):
#     test = Test(arr=[i, 1, 2, 3])
#     arr.append(test.arr)
# print(time.time() - now)
# print(arr)
# type_adapter = TypeAdapter(test)
# print(type_adapter.validator)
# print(type_adapter.validate_python(()))