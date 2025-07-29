import pytest
import logging
from UPR_LDA.documents_fetcher.document_fetcher import PDFFetcher
from UPR_LDA.documents_fetcher.document_cache import InMemoryDocumentCache

logger = logging.Logger(__name__)

class TestDocumentFetcher:
    
    _DUMMY_PDF_URL = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
    _DUMMY_PDF_CONTENT = "Dummy PDF file\n\n"

    @pytest.mark.asyncio
    async def test_fetching_a_document(self) -> None:
        fetcher = PDFFetcher()
        document = await fetcher.fetch(url=self._DUMMY_PDF_URL)
        assert document.content == self._DUMMY_PDF_CONTENT

    @pytest.mark.asyncio
    async def test_fetching_from_cache(self) -> None:
        fetcher = PDFFetcher(cache=InMemoryDocumentCache())
        document = await fetcher.fetch(url=self._DUMMY_PDF_URL)
        assert document.content == self._DUMMY_PDF_CONTENT

        document = await fetcher.fetch(key=document.key)
        assert document.content == self._DUMMY_PDF_CONTENT





