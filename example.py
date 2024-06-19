import abc
import datetime
import decimal
import enum
import time
import typing
import uuid
from typing import List, Dict, Optional
from fast_serializer import FastDataclass, field
from fast_serializer.type_parser import type_parser
from fast_serializer.validator import StringValidator, BytesValidator, BoolValidator, IntegerValidator, UuidValidator, \
    DatetimeValidator, TimeValidator, TimedeltaValidator, LiteralValidator


# class Test(enum.Enum):
#     COLOR = 'red'
#
#     BLUE = 1
#
#
# class Address(FastDataclass):
#     """地址"""
#     detail_address: str
#
#
# class User(FastDataclass):
#     """用户"""
#     tu: typing.Tuple[int, str]
#     # address_list: List[Address]


class Test(FastDataclass):
    arr: str


arr = []
now = time.time()
for i in range(20):
    arr.append(Test(arr='asd'))
print(time.time() - now)
# print(typing.get_args(typing.Tuple[int, str, ...]))
# print(LiteralValidator.build(typing.Literal[1, 2, 3]))
# print(type_parser.is_tuple(typing.Tuple[int, str]))
# print(issubclass(Test, enum.Enum))
# user = User(tu=1)
# print(user)
# print(typing.get_origin(typing.Literal[1, 2, 3]))
# print(issubclass(typing.Literal[1, 2, 3], typing.Literal))
# print(datetime.datetime.fromisoformat("2023-06-11T10:15:30"))
# print(time.time())
# print(len(str(time.time() * 1000)))
# print(TimeValidator().validate(datetime.datetime.now()))
# print(DatetimeValidator().validate(time.time()))
# print(IntegerValidator().validate('123'))
# print(BoolValidator().validate('yes'))
# print(issubclass(tuple, typing.Collection))
# print(isinstance(decimal.Decimal('11'), decimal.Decimal))
# print(User.dataclass_fields)

# if isinstance(123, (int, float, decimal.Decimal, enum.Enum, bool)):
#     print(123)
# print(StringValidator().validate(123, allow_number=True))
# 数据
# data = {'nickname': 'Lao Da', 'address_list': [{'detail_address': 'China'}]}
#
# # JSON字典到Python对象反序列化的用法
# user = User(**data)
# print(user)  # 提供了Repr
# # > 'User(nickname='Lao Da', age=None)'
# print(user.nickname)
# # > 'Lao Da'
#
# print(type([]) is List)
# # print(isinstance([{}], List[Address]))