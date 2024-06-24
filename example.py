import datetime
import typing
import uuid
from types import NoneType
from typing import Iterable, Collection, Optional

from fast_serializer import FastDataclass, field


class Test(FastDataclass):
    pass

    # name: datetime.time = field(val_extra=dict(mode='time'))
    arr: dict[str]


haha = dict(aa='asd')

print(haha.pop('aa'))
print(haha.pop('bb'))
print(haha)
# print(Test.dataclass_fields['arr'].validator)
# for i in {'asd': 1, 'bbb': 2}.keys():
#     print(i)
# test = Test(arr=dict())
# print(test.arr)
# print(getattr(Optional, '_name'))
# print(Optional[list[str]] is Optional)
# print(typing.get_origin(Optional) == NoneType)
# print(Test.dataclass_fields['arr'].validator)
# test = Test(name=900, arr=['sad'])
# print(test.name)
# print(test.arr)