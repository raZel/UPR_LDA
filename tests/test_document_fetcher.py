import pytest
import logging
from UPR_LDA.documents_fetcher.document_fetcher import DocumentFetcher

logger = logging.Logger(__name__)

@pytest.mark.asyncio
async def test_fetching_a_document() -> None:
    url = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
    fetcher = DocumentFetcher()
    document = await fetcher.fetch(url)
    assert document
