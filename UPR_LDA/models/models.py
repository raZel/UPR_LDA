import typing
from pydantic import BaseModel
from enum import Enum

class UPRCycle(str, Enum):
    FIRST = "First"
    SECOND = "Second"
    THIRD = "Third"
    FOURTH = "Fourth"

ModelKey = str
class FileType(str, Enum):
    PDF = "pdf"
    TEXT = "txt"

class FileMetadata(BaseModel):
    key: ModelKey
    file_type: FileType

class FileData(BaseModel):
    content: bytes
    metadata: FileMetadata

    @property
    def key(self) -> ModelKey:
        return self.metadata.key

class DocumentMetaData(BaseModel):
    key: typing.Optional[ModelKey] = None
    url: str

class UPRCivilSocietyTags(BaseModel):
    country: typing.Optional[str] = None
    cycle: typing.Optional[str] = None
    organization_name: typing.Optional[str] = None

class UPRDocumentMetaData(DocumentMetaData, UPRCivilSocietyTags):
    pdf_file: typing.Optional[FileMetadata] = None
    text_file: typing.Optional[FileMetadata] = None
    region: typing.Optional[str] = None
    is_oecd: typing.Optional[bool] = None
    income_level: typing.Optional[str] = None
    democracy_level: typing.Optional[str] = None


