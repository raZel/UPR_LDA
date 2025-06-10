import os
from UPR_LDA import models
import aiofiles

class DocumentCache:
    def __init__(self, cache_dir: str):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_cache_path(self, document_key: models.DocumentKey):
        filename = document_key.as_string()
        return os.path.join(self.cache_dir, filename)

    async def save(self, document: models.Document):
        path = self._get_cache_path(document.key)
        async with aiofiles.open(path, 'w', encoding='utf-8') as f:
            await f.write(document.model_dump_json())
        

    async def load(self, document_key: models.DocumentKey) -> models.Document:
        path = self._get_cache_path(document_key)
        async with aiofiles.open(path, 'r', encoding='utf-8') as f:
            data = await f.read()
        return models.Document.model_validate_json(data)