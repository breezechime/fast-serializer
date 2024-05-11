# -*- coding:utf-8 -*-
import dataclasses


@dataclasses.dataclass
class DataclassConfig(object):
    """数据类配置"""

    """"""
    init: bool = True

    repr: bool = True

    eq: bool = True

    order: bool = False

    unsafe_hash: bool = False

    frozen: bool = False

    datetime_format: str = "%Y-%m-%d %H:%M:%S"

    date_format: str = '%Y-%m-%d'

    title: str = None

    description: str = None