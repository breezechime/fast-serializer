# -*- coding:utf-8 -*-
import decimal
import uuid
from typing import Any

from pydantic import BaseModel, field_validator, ValidationError, ConfigDict, Field
from pydantic_core import PydanticCustomError


class Test(BaseModel):

    model_config = ConfigDict(str_to_upper=True)

    test2: uuid.UUID

    # @field_validator('test2', mode='before')
    # def val_name(cls, v):
    #     raise UnicodeDecodeError('utf-8', b'test', 0, 1, 'test')

test = Test(test2='asd')
print(test.test2)
# try:
#     Test(test=123, test2='asd', arr=[1, 2])
# except ValidationError as e:
#     print(e.json())
# for i in dir(Test):
#     print(i, getattr(Test, i))
# core_schema.set_schema()
# ada = TypeAdapter(Test)
# print(ada.validator)
# deque = collections.deque(('2'))
# print(list(deque))
# print(deque)
# print(issubclass(collections.deque, Collection))
# test = Test(arr=['1'])
# print(test.arr)
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
