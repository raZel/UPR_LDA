import os
from UPR_LDA import models
import aiofiles
import abc
import typing
import json
import logging

_logger = logging.getLogger(__name__)

class DocumentCache:
    @abc.abstractmethod
    async def save(self, document: models.FileData) -> bool:
        pass

    @abc.abstractmethod
    async def load(self, document_key: str) -> typing.Optional[models.FileData]:
        pass

class NOOPDocumentCache(DocumentCache):
    async def save(self, document: models.FileData) -> bool:
        return False

    async def load(self, document_key: str) -> typing.Optional[models.FileData]:
        return None

class InMemoryDocumentCache(DocumentCache):
    def __init__(self):
        self._cache = {}

    async def save(self, document: models.FileData) -> bool:
        self._cache[document.key] = document
        return True

    async def load(self, document_key: str) -> typing.Optional[models.FileData]:
        return self._cache.get(document_key)

class FSDocumentCache(DocumentCache):
    """
    saves and loads documents in json format to the file system in the following location
    cache_dir/document_key
    """
    def __init__(self, cache_dir: str):
        _logger.debug("Initializing FSCache in dir: %s", cache_dir)
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_content_dir(self, document_key: str):
        dir = os.path.join(self.cache_dir, f"{document_key}-content")
        os.makedirs(dir, exist_ok=True)
        return dir
    
    def _get_content_path(self, document_key: str):
        return os.path.join(self._get_content_dir(document_key), f"{document_key}")

    def _get_metadata_path(self, document_key: str):
        return os.path.join(self._get_content_dir(document_key), f"{document_key}.metadata.json")

    async def save(self, document: models.FileData) -> bool:
        content_path = self._get_content_path(document.key)
        metadata_path = self._get_metadata_path(document.key)
        try:
            # Save content
            async with aiofiles.open(content_path, 'wb') as f:
                await f.write(document.content)

            # Save metadata
            async with aiofiles.open(metadata_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(document.metadata.model_dump()))
            return True
        except Exception:
            _logger.exception("Failed saving document %s to cache", document)
            return False
        

    async def load(self, document_key: str) -> typing.Optional[models.FileData]:
        content_path = self._get_content_path(document_key)
        metadata_path = self._get_metadata_path(document_key)
        try:
            # Load metadata
            async with aiofiles.open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.loads(await f.read())

            # Load content
            async with aiofiles.open(content_path, 'rb') as f:
                content = await f.read()

            # Reconstruct FileData from loaded metadata and content
            loaded_metadata = models.FileMetadata(**metadata)
            loaded_document = models.FileData(content=content, metadata=loaded_metadata)
            return loaded_document
        except Exception as e:
            _logger.exception("Failed loading document_key %s from cache", document_key)
            return None
