# -*- coding:utf-8 -*-
import collections
import datetime
import decimal
import queue
import time
import typing
import uuid
from typing_extensions import TypedDict
from typing import Union, Collection, Iterable, Mapping
from typing_extensions import Literal
from pydantic_core import PydanticCustomError, ErrorDetails, SchemaValidator
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator, TypeAdapter, Field
from fast_serializer.validator import TargetTypeValidator, DatetimeValidator, DateValidator
from pydantic_core import core_schema


# core_schema.
def printaa():
    print(123)


class BB(TypedDict):

    name: str


class Test(BaseModel):

    model_config = ConfigDict()

    arr: typing.Deque

    # @field_validator('name')
    # def val_name(cls, v):
    #     if v == 'bar':
    #         raise ValueError('haha')
    #     return v


ada = TypeAdapter(Test)
print(ada.validator)
deque = collections.deque()
print(deque)
test = Test(arr=['1'])
print(test.arr)
# schema = core_schema.tuple_schema(
#         [core_schema.int_schema(), core_schema.str_schema()],
#         variadic_item_index=1,
#     )
# v = SchemaValidator(schema)
# v.validate_python((1, 'hello', 1))
# print(typing.get_args(typing.Optional[str]))
# print(typing.get_origin(str))
# test = Test(time='-1DT12H30M5S')
# print(test.time)
# datetime.timedelta
# print(datetime.date.fromisoformat('2023-06-11'))
# datetime.timedelta
# core_schema.timedelta
# print(len("2023-06-11T10:15:30.123"))
# print(DateValidator.str_to_date("2023-06-11T10:15:30.123+02:00"))
# print(datetime.MINYEAR)
# print(Test.model_fields)


# ada.validate_python({'time': ['1', 1]})

# print(datetime.datetime.strptime("2021-01-01 00:00", "%Y-%m-%d %H"))
# test = Test(time='2023-06-11T10:15:30Z')
# print(test.time)
# print(issubclass(list, Collection))
# print(issubclass(tuple, Collection))
# print(issubclass(set, Collection))
# print(issubclass(frozenset, Collection))
# print(issubclass(frozenset, Iterable))
# res = ada.validate_python({'time': time.time() * 1000})
# print(res.time)

# print(datetime.datetime.fromtimestamp(time.time()))
# print(DatetimeValidator.timestamp_to_datetime(time.time()))
# print(datetime.datetime.strptime('2021-01-01 00:00:00', '%Y-%m-%d'))
# print(ada.validator)
# error = ErrorDetails()
# try:
#     test = Test(name='bar')
# except PydanticCustomError as e:
#     print(e.json())
    # print(dir(e))
    # print(type(e.errors()[0]))
    # print(e)
# raise PydanticCustomError(
#     'not_a_bar',
#     'not a bar',
# )
# try:
#     raise ValueError('test', 'aaa')
# except ValueError as e:
#     print(e.__dict__)
#     print(dir(e))
# try:
#     test = Test(name=123)
# except ValidationError as e:
#     print(e.json())
#     print(dir(e))
    # print(type(e.errors()[0]))
    # print(e)