import datetime
import decimal
import enum
import uuid
from inspect import _ParameterKind  # type: ignore
from typing import Union, Literal

from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from typing_extensions import TypedDict
from fast_serializer import FastDataclass, field
from dataclasses import dataclass


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


class Test(FastDataclass):
    name: tuple[str, ...]


# print(str(datetime.timedelta(hours=59, minutes=2)))
# Test.dataclass_fields['name'].serializer.to_python()
a = Test(name=('阿圣诞节啊是', 'asd'))
# a.name = (1, 'asd', 2)
print(a.to_json_str(ensure_ascii=False))
