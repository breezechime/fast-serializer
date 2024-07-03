# -*- coding:utf-8 -*-
from sqlalchemy import TypeDecorator, Integer


class IntEnum(TypeDecorator):
    """整数枚举"""

    imp = Integer