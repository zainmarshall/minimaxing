# This file can be used to define Pydantic models for request/response schemas

from pydantic import BaseModel

class ExampleModel(BaseModel):
    name: str
    value: int
