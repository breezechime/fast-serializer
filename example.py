import decimal
import enum
from typing import List, Dict, Optional
from fast_serializer import FastDataclass, field
from fast_serializer.validator import StringValidator


class Address(FastDataclass):
    """地址"""
    detail_address: str


class User(FastDataclass):
    """用户"""
    nickname: str = field(required=True)
    age: int = None

    level: int = 1
    # address_list: List[Address]


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