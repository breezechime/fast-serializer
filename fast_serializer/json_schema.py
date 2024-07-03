# -*- coding:utf-8 -*-
from typing import Dict, Any


class JsonSchema:
    """JSON schemas"""

    schema_draft = 'https://json-schema.org/draft/2020-12/schema'

    def __init__(self):
        self.schema_definition: Dict[str, Any] = {}

    @classmethod
    def generate(cls, dataclass):
        pass