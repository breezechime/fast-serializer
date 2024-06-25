import time
from fast_serializer import FastDataclass


class Test(FastDataclass):

    arr: list[int]


now = time.time()
arr = []
for i in range(1000):
    test = Test(arr=[i, '2', 3.0])
    arr.append(test.arr)
print(time.time() - now)
# print(arr)