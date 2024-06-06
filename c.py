# -*- coding:utf-8 -*-
import datetime
from pydantic_core import PydanticCustomError, ErrorDetails
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator


class Test(BaseModel):

    model_config = ConfigDict()

    name: str

    @field_validator('name')
    def val_name(cls, v):
        if v == 'bar':
            raise ValueError('haha')
        return v


# error = ErrorDetails()
try:
    test = Test(name='bar')
except PydanticCustomError as e:
    # print(e.json())
    print(dir(e))
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