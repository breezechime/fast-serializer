import decimal
from typing import Mapping, Iterable

import cython

def isinstance_safe(v, tp) -> cython.int:
    try:
        return isinstance(v, tp)
    except (Exception,) as e:
        return False

def check_is_iterable(v) -> cython.int:
    """检查是否为可迭代对象"""
    if isinstance_safe(v, (list, tuple, set, frozenset)):
        return True
    elif not isinstance_safe(v, (str, bytes, bytearray, dict, Mapping)) and isinstance_safe(v, Iterable):
        return True
    return False

def maybe_str(v) -> str:
    if isinstance_safe(v, str):
        return v
    elif isinstance_safe(v, bytes):
        return v.decode('utf-8')
    return ''


@cython.wraparound(False)
@cython.boundscheck(False)
def validate_int(v) -> cython.int:
    if isinstance_safe(v, int):
        return v
    _maybe_str = maybe_str(v)
    if _maybe_str != '':
        return int(_maybe_str)
    # try:
    #     _maybe_str = maybe_str(v)
    #     if _maybe_str:
    #         return int(_maybe_str)
    # except (ValueError, TypeError, UnicodeError) as e:
    #     raise ValueError(f'should be int {e}')
    if isinstance_safe(v, (float, decimal.Decimal)):
        return int(v)
    raise ValueError('should be int')

@cython.wraparound(False)
@cython.boundscheck(False)
def validate_list(v):
    if not check_is_iterable(v):
        raise ValueError('should be list')

    cdef list res
    res = []
    for i in v:
        res.append(validate_int(i))
    return res