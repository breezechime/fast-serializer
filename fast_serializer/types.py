# -*- coding:utf-8 -*-
import decimal
from typing import (
    Optional, Union, Literal
)


optional = Optional

number = Union[int, float, decimal.Decimal]

DeserializeError = Literal['strict', 'warn', 'ignore']

SerializeError = Literal['warn', 'error', 'ignore']