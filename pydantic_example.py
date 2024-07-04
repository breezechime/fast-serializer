import enum
import inspect
import time
import typing
from typing import Callable, Union, Generator, NamedTuple, Sequence, Type, TypeVar, Iterable

from pydantic import BaseModel, TypeAdapter, InstanceOf, Field
from pydantic_core import core_schema, ArgsKwargs
from typing_extensions import TypedDict


def test(v: int, a: int):
    print(v)
    # print(kwargs)
    # print(args)
    # print(kwargs)
    # print(args)
    # print(kwargs)


class Point(NamedTuple):
    x: int
    y: int


class AType(enum.StrEnum):
    RED = 'a'


Foobar = TypeVar('Foobar')
BoundFloat = TypeVar('BoundFloat', bound=float)
IntStr = TypeVar('IntStr', int, str)


class HaHa(TypedDict):
    name: str


class Test(BaseModel):

    arr: test


# print(Test.__pydantic_validator__)
# args = ArgsKwargs()
# print(args.args)
map = {'v': 123, 'a': 222, 'c': 123}
a = Test(arr=map)
print(map)