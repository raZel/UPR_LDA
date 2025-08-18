from UPR_LDA.data_store import CSVDataStore
from UPR_LDA.models import ModelKey, UPRDocumentMetaData
from UPR_LDA.html_crawler import crawl_upr_for_civil_society_submissions
import tempfile
import logging
import os
import pytest

logger = logging.Logger(__name__)

class TestHtmlCrawl:
    @pytest.mark.asyncio
    async def test_crawl_upr(self) -> None:
        results = await crawl_upr_for_civil_society_submissions("https://www.ohchr.org/en/hr-bodies/upr/documentation")
        assert len(results) != 0
