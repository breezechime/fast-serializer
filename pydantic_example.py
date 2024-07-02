import enum
import inspect
import time
import typing
from typing import Callable, Union, Generator, NamedTuple, Sequence, Type, TypeVar, Iterable

from pydantic import BaseModel, TypeAdapter, InstanceOf, Field
from pydantic_core import core_schema
from typing_extensions import TypedDict


def test(a, *args, **kwargs):
    pass
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


for k, v in inspect.signature(test).parameters.items():
    print(k)
    print(v.kind)
