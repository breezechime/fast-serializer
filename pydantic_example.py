import enum
import time

from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from typing_extensions import TypedDict
from fast_serializer import FastDataclass


class AType(enum.IntEnum):
    RED = 1

    BLUE = 2


class HaHa(TypedDict, total=False):
    name: int


engine = create_engine('sqlite:///test.db')
Base = declarative_base()
SessionFactory = sessionmaker(bind=engine)
session = SessionFactory()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64))


class Test(BaseModel):
    name: list[str]


now = time.time()
arr = []
for i in range(10000):
    a = Test(name=('阿圣诞节啊是', 'asd'))
    arr.append(a)

print(time.time() - now)
# a = Test(name=('阿圣诞节啊是', 1))
# value = a.to_dict()
# print(value)