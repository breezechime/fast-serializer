import decimal
import time
import uuid

from fast_serializer import FastDataclass, field


class Test(FastDataclass):

    name: uuid.UUID = field(val_extra=dict(version=4))


print(str(uuid.uuid1()))
test = Test(name='79585ecf-3091-11ef-b16c-085bd678a05b')
print(test.name)