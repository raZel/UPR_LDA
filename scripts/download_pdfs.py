import logging
from UPR_LDA.utils import get_settings, init_logger, get_data_store, get_pdf_fetcher, get_fs_cache
import asyncio
from UPR_LDA.data_store import UPRDataStore
from UPR_LDA.documents_fetcher.document_cache import FSDocumentCache
from UPR_LDA.documents_fetcher.document_fetcher import PDFFetcher
from UPR_LDA.documents_fetcher.pdf_utils import PdfUtils
from UPR_LDA.models import UPRDocumentMetaData, FileData, FileMetadata, FileType

init_logger()
_logger = logging.getLogger(__name__)


async def download_single_doc(doc: UPRDocumentMetaData, store: UPRDataStore, fetcher: PDFFetcher, cache: FSDocumentCache):
    _logger.info("fetching pdf for doc: %s", doc.key)
    try:
        pdf_file_key = f"{doc.key}.pdf"
        file_data = await fetcher.fetch(url=doc.url, key=pdf_file_key)
        doc.pdf_file = file_data.metadata
        text_content = await PdfUtils.pdf_to_text(file_data.content)
        if len(text_content) == 0:
            raise ValueError("empty pdf_to_text")
        text_file_key = f"{doc.key}.txt"
        text_data = FileData(content=text_content.encode(), metadata=FileMetadata(key=text_file_key, file_type=FileType.TEXT))
        success = await cache.save(text_data)
        if not success:
            raise ValueError("failed cache save")
        doc.text_file = text_data.metadata
        with store.autoPersist:
            store.add_or_update(doc)
        _logger.info("downloaded pdf for doc: %s", doc.key)
    except Exception as e:
        _logger.error("failed to fetch pdf for doc: %s, url: %s, error: %s", doc.key, doc.url, e)
        raise

async def main():
    """
    Main function to run the UPR scraper.
    """
    # Load environment variables from .env file

    _logger.info(f"Starting to download pdfs")
    store = get_data_store()
    fetcher = get_pdf_fetcher()
    cache = get_fs_cache()
    docs_to_download = [doc for doc in store.all() if not doc.pdf_file and doc.url][:2]
    _logger.info("Downloading %s documents", len(docs_to_download))
    tasks = [download_single_doc(doc, store, fetcher, cache) for doc in docs_to_download]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    num_fail = len([res for res in results if isinstance(res, Exception)])
    _logger.info(f"Finished downloading pdfs. out of %s, succes: %s, fail: %s", 
                 len(docs_to_download), 
                 len(docs_to_download) - num_fail,
                 num_fail)


if __name__ == "__main__":
    asyncio.run(main())