import uuid
from typing import Iterable
from fast_serializer import FastDataclass, field


class Test(FastDataclass):

    name: uuid.UUID = field()


test = Test(name=Iterable)
print(test.name)