from dotenv import load_dotenv, dotenv_values
import logging
import re
from unidecode import unidecode
from pydantic import BaseModel
import typing
from UPR_LDA.data_store import UPRDataStore
from UPR_LDA.models.models import UPRDocumentMetaData
from UPR_LDA.documents_fetcher.document_cache import FSDocumentCache
from UPR_LDA.documents_fetcher.document_fetcher import PDFFetcher

_logger = logging.getLogger(__name__)

def init_logger():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class Settings(BaseModel):
    _UPR_DOCUMENT_CACHE_DIR: str = "data/upr_document_cache"
    _UPR_METADATA_FILE: str = "data/upr_metadata.json"

    @property
    def upr_metadata_file_path(self) -> str:
        return self._UPR_METADATA_FILE

    @property
    def upr_document_cache_dir(self) -> str:
        return self._UPR_DOCUMENT_CACHE_DIR

_settings: typing.Optional[Settings] = None
def get_settings() -> Settings:
    global _settings
    """Load environment variables from .env file."""
    if _settings:
        return _settings
    
    _logger.info("Loading environment variables from .env file")
    config = dotenv_values()
    _settings = Settings(**config)
    return _settings

_store = None
def get_data_store() -> UPRDataStore:
    global _store
    if _store is None:
        json_path = get_settings().upr_metadata_file_path
        _store = UPRDataStore(json_path=json_path)
    return _store

def get_cache_dir() -> str:
    return get_settings().upr_document_cache_dir

_fs_cache = None
def get_fs_cache() -> FSDocumentCache:
    global _fs_cache
    if _fs_cache is None:
        cache_dir = get_settings().upr_document_cache_dir
        _fs_cache = FSDocumentCache(cache_dir)
    return _fs_cache
    
    
_pdf_fetcher = None
def get_pdf_fetcher() -> PDFFetcher:
    global _pdf_fetcher
    if _pdf_fetcher is None:
        _pdf_fetcher = PDFFetcher(cache=get_fs_cache())
    return _pdf_fetcher

def clean_country_name(text: str) -> str:
    """
    Cleans a string by:
    1. Transliterating it to ASCII using unidecode.
    2. Removing a set of problematic characters.
    """
    _PROBLEMATIC_CHARACTERS_PATTERN = r'[\[\]{}()"\'\\/?,.]'
    # First, transliterate to the closest ASCII representation
    cleaned_text = unidecode(text)
    # Then, remove any remaining problematic characters
    return re.sub(_PROBLEMATIC_CHARACTERS_PATTERN, '', cleaned_text)