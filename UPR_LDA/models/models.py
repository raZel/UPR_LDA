import typing
from pydantic import BaseModel

class Document(BaseModel):
    key: str
    url: str
    content: str



