# -*- coding:utf-8 -*-
import datetime
import decimal
import uuid
from typing import Union
from typing_extensions import Literal
from pydantic_core import PydanticCustomError, ErrorDetails
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator, TypeAdapter

from fast_serializer.validator import TargetTypeValidator


def printaa():
    print(123)


class Test(BaseModel):

    model_config = ConfigDict()

    name: Literal['aaa', 'bbb', 123]

    # @field_validator('name')
    # def val_name(cls, v):
    #     if v == 'bar':
    #         raise ValueError('haha')
    #     return v


class Action:

    name: str


# print(Test.model_fields)
ada = TypeAdapter(Test)
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