"""
documents_fetcher is responsible for retrieving documents
to be processed, fetching a document requires downloading
a pdf version of it from a url and transforming it to a txt file.
"""

import typing
import abc
import logging
from UPR_LDA.models import FileData, FileMetadata, FileType
from .document_cache import DocumentCache, NOOPDocumentCache
import hashlib
import aiohttp

_logger = logging.getLogger(__name__)
class DocumentFetcher(abc.ABC):
    def __init__(self) -> None:
       self.session = aiohttp.ClientSession()

    async def download(self, url) -> bytes:
        async with self.session.get(url) as response:
            try:
                response.raise_for_status()
                return await response.read()
            except aiohttp.ClientResponseError:
                _logger.error(f"Request to {url} failed with status {response.status}. Response: {await response.text()}")
                raise

    @abc.abstractmethod
    async def fetch(self, url: str, key: typing.Optional[str] = None) -> FileData:
        pass

class PDFFetcher(DocumentFetcher):
    def __init__(self, cache: DocumentCache = NOOPDocumentCache()):
        super().__init__()
        self.cache = cache

    async def fetch(self, url: typing.Optional[str] = None, key: typing.Optional[str] = None, check_cache_only: bool = False) -> FileData:
        """
            fetch document from url.
            optionally use key as identifier for the document mainly for caching
            if no key provided hash the url to get a key
            important, duplicates are only checked with the key, not the content.
            fetching the same url with different keys will save duplicates.
        """
        _logger.debug("fetch called with args: %s", locals())
        if key:
            document_key = key
        elif url:
            document_key = hashlib.md5(url.encode()).hexdigest() + ".pdf"
        else:
            raise ValueError("Either url or key must be provided")
        
        _logger.debug("checking cache. document_key: %s", document_key)
        doc = await self.cache.load(document_key)
        if doc:
            return doc
        _logger.debug("document not in cache. document_key: %s", document_key)
        if check_cache_only:
            raise ValueError("not in cache and check_cache_only: %s", check_cache_only)

        if not url:
            raise ValueError("no url to fetch")
        _logger.info("fetching document. url: %s", url)
        doc_bytes = await self.download(url)
        doc = FileData(content=doc_bytes, metadata=FileMetadata(
            key=document_key,
            type=FileType.PDF,
        ))
        saved = await self.cache.save(doc)
        if not saved:
            _logger.warning("failed saving to cache. doc: %s", doc)
        return doc



    
