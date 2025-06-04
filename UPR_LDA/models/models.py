import typing
from pydantic import BaseModel

class DocumentKey(BaseModel):
    value: str

    def as_string(self) -> str:
        return self.value

class Document(BaseModel):
    key: typing.Optional[DocumentKey] = None
    url: str
    content: str



