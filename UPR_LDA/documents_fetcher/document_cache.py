import os
from UPR_LDA import models
import aiofiles
import abc
import typing
import logging

_logger = logging.getLogger(__name__)

class DocumentCache:
    @abc.abstractmethod
    async def save(self, document: models.DocumentData) -> bool:
        pass

    @abc.abstractmethod
    async def load(self, document_key: str) -> typing.Optional[models.DocumentData]:
        pass

class NOOPDocumentCache(DocumentCache):
    async def save(self, document: models.DocumentData) -> bool:
        return False

    async def load(self, document_key: str) -> typing.Optional[models.DocumentData]:
        return None

class InMemoryDocumentCache(DocumentCache):
    def __init__(self):
        self._cache = {}

    async def save(self, document: models.DocumentData) -> bool:
        self._cache[document.key] = document
        return True

    async def load(self, document_key: str) -> typing.Optional[models.DocumentData]:
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

    def _get_cache_path(self, document_key: str):
        return os.path.join(self.cache_dir, document_key)

    async def save(self, document: models.DocumentData) -> bool:
        path = self._get_cache_path(document.key)
        try:
            async with aiofiles.open(path, 'w', encoding='utf-8') as f:
                await f.write(document.model_dump_json())
            return True
        except Exception:
            _logger.exception("Failed saving document %s to cache", document)
            return False
        

    async def load(self, document_key: str) -> typing.Optional[models.DocumentData]:
        path = self._get_cache_path(document_key)
        try:
            async with aiofiles.open(path, 'r', encoding='utf-8') as f:
                data = await f.read()
            return models.DocumentData.model_validate_json(data)
        except Exception as e:
            _logger.exception("Failed loading document_key %s from cache", document_key)
            return None

