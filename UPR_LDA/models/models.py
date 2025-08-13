import typing
from pydantic import BaseModel

ModelKey = str

class DocumentData(BaseModel):
    key: ModelKey
    url: str
    content: str

class DocumentMetaData(BaseModel):
    key: typing.Optional[ModelKey] = None
    url: str

class UPRCivilSocietyTags(BaseModel):
    country: typing.Optional[str] = None
    cycle: typing.Optional[str] = None
    #TODO: add more tags that will be parsed from the html

class UPRDocumentMetaData(DocumentMetaData, UPRCivilSocietyTags):
    continent: typing.Optional[str] = None
