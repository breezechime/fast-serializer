import enum
import time
import typing

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from typing_extensions import TypedDict
from fast_serializer import FastDataclass, DataclassConfig


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
    model_config = ConfigDict(extra='allow')

    name: str = Field(frozen=True)


a = Test(name='asd')
a.__pydantic_extra__ = {'bb': 123}
print(a.model_extra)
# a.name = 'bbb'