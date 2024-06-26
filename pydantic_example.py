import time
from typing import Callable

from pydantic import BaseModel, TypeAdapter, InstanceOf
from pydantic_core import core_schema


def test():
    pass
    # print(args)
    # print(kwargs)


class Test(BaseModel):

    arr: test


print(Test.__pydantic_validator__)
val = core_schema.str_schema()
print(val)
# print(val)
# print(Test.__pydantic_validator__)
# print(Test(arr=(1, 2)))
# now = time.time()
# arr = []
# for i in range(100000):
#     test = Test(arr=[i, 1, 2, 3])
#     arr.append(test.arr)
# print(time.time() - now)
# print(arr)
# type_adapter = TypeAdapter(test)
# print(type_adapter.validator)
# print(type_adapter.validate_python(()))