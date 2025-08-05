import typing
from pydantic import BaseModel

ModelKey = str

class Document(BaseModel):
    key: ModelKey
    url: str
    content: str

class DocumentMetaData(BaseModel):
    key: ModelKey
    url: str

class UPRDocumentMetaData(DocumentMetaData):
    country: typing.Optional[str] = None
    continent: typing.Optional[str] = None
    cycle: typing.Optional[str] = None




