"""
documents_fetcher is responsible for retrieving documents
to be processed, fetching a document requires downloading
a pdf version of it from a url and transforming it to a txt file.
"""

import typing
import abc
import logging
from UPR_LDA.models import Document
from .document_downloader import DocumentDownloader
from .document_transformer import DocumentTransformer
from .document_cache import DocumentCache

logger = logging.getLogger(__name__)

class DocumentFetcher(abc.ABC):
    def __init__(self):
        self.downloader = DocumentDownloader()
        self.transformer = DocumentTransformer()

    async def fetch(self, url: str) -> Document:
        # logger.info("fetching document. document_key: %s, url: %s", document_key, url)
        # # check if in cache
        # if self.cache:
        #     try:
        #         logger.info("fetching from cache. document_key: %s, url: %s", document_key, url)
        #         return await self.cache.load(document_key)
        #     except Exception:
        #         logger.exception("failed fetching from cache. document_key: %s, url: %s", document_key, url)
        
        logger.info("fetching document. url: %s", url)
        doc_bytes = await self.downloader.download(url)
        doc_str = await self.transformer.pdf_to_text(doc_bytes)
        return Document(url=url, content=doc_str)



    

