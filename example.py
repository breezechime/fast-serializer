import datetime
import uuid
from typing import Iterable

from fast_serializer import FastDataclass, field


class Test(FastDataclass):

    name: datetime.time = field(val_extra=dict(mode='time'))


test = Test(name=90)
print(test.name)