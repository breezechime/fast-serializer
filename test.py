import time
from typing import Mapping, Iterable
import c_utils


def isinstance_safe(v, tp):
    try:
        return isinstance(v, tp)
    except (Exception,) as e:
        return False


def check_is_iterable(v):
    """检查是否为可迭代对象"""
    if isinstance_safe(v, (list, tuple, set, frozenset)):
        return True
    elif not isinstance_safe(v, (str, bytes, bytearray, dict, Mapping)) and isinstance_safe(v, Iterable):
        return True
    return False


def validate_list(v):
    res = check_is_iterable(v)
    if not res:
        raise ValueError('should be list')
    return [int(i) for i in v]


now = time.time()
arr = []
for i in range(100000):
    # arr.append(i)
    res = c_utils.validate_list([i, 1, 2, 3])
    # arr.append(res)
print(time.time() - now)
# print(arr)