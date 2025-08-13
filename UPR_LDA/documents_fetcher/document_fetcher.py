"""
documents_fetcher is responsible for retrieving documents
to be processed, fetching a document requires downloading
a pdf version of it from a url and transforming it to a txt file.
"""

import typing
import abc
import logging
from UPR_LDA.models import DocumentData
from .pdf_utils import PdfUtils
from .document_cache import DocumentCache, NOOPDocumentCache, FSDocumentCache
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
    async def fetch(self, url: str, key: typing.Optional[str] = None) -> DocumentData:
        pass

class PDFFetcher(DocumentFetcher):
    def __init__(self, cache: DocumentCache = NOOPDocumentCache()):
        super().__init__()
        self.cache = cache

    async def fetch(self, url: typing.Optional[str] = None, key: typing.Optional[str] = None) -> DocumentData:
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
            document_key = hashlib.md5(url.encode()).hexdigest()
        else:
            raise ValueError("Either url or key must be provided")
        
        _logger.debug("checking cache. document_key: %s", document_key)
        doc = await self.cache.load(document_key)
        if doc:
            return doc
        _logger.debug("document not in cache. document_key: %s", document_key)

        if not url:
            raise ValueError("no url to fetch")
        _logger.info("fetching document. url: %s", url)
        doc_bytes = await self.download(url)
        doc_str = await PdfUtils.pdf_to_text(doc_bytes)
        doc = DocumentData(url=url, content=doc_str, key=document_key)
        saved = await self.cache.save(doc)
        _logger.warning("failed saving to cache. doc: %s", doc)
        return doc



    
