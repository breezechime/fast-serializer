# -*- coding:utf-8 -*-
import uuid
from pydantic import BaseModel, ConfigDict, Field


class Test(BaseModel):

    model_config = ConfigDict(str_to_upper=True)

    uid: uuid.UUID = Field(version=1)


print(Test.__pydantic_validator__)
Test(uid='41a79522-316a-11ef-bf27-56f55720ded6')
