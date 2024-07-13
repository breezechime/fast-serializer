import datetime
import decimal
import enum
import uuid
from typing import NamedTuple, TypeVar, Union, Literal

from pydantic import BaseModel, Field, ConfigDict
from pydantic_core import PydanticSerializationUnexpectedValue
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
from typing_extensions import TypedDict


def test(v: int, a: int):
    print(v)
    # print(kwargs)
    # print(args)
    # print(kwargs)
    # print(args)
    # print(kwargs)


class Point(NamedTuple):
    x: int
    y: int


class AType(enum.Enum):
    RED = Point(1, 0)


Foobar = TypeVar('Foobar')
BoundFloat = TypeVar('BoundFloat', bound=float)
IntStr = TypeVar('IntStr', int, str)


class HaHa(TypedDict):
    name: str


engine = create_engine('sqlite:///test.db')
Base = declarative_base()
SessionFactory = sessionmaker(bind=engine)
session = SessionFactory()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64))


Base.metadata.create_all(engine)


class Test(BaseModel):

    model_config = ConfigDict(from_attributes=True, use_enum_values=False)

    # id: str
    name: tuple[str, int]


# print(Test.__pydantic_serializer__)
aa = Test(name=('a', 1))
aa.name = ('a', 'asd')
print(aa.model_dump(mode='json'))