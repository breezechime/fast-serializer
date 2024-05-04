from typing import List, Dict
from fast_serializer import FastDataclass, field


class Address(FastDataclass):
    """地址"""
    detail_address: str


class User(FastDataclass):
    """用户"""
    nickname: str = field(required=True)
    age: int = None
    # address_list: List[Address]


# 数据
data = {'nickname': 'Lao Da', 'address_list': [{'detail_address': 'China'}]}

# JSON字典到Python对象反序列化的用法
user = User(**data)
print(user)  # 提供了Repr
# > 'User(nickname='Lao Da', age=None)'
print(user.nickname)
# > 'Lao Da'

print(type([]) is List)
# print(isinstance([{}], List[Address]))