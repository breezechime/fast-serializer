import time
from pydantic import BaseModel


class Test(BaseModel):

    arr: list[int]


now = time.time()
arr = []
for i in range(100000):
    test = Test(arr=[i, 1, 2, 3])
    arr.append(test.arr)
print(time.time() - now)
# print(arr)