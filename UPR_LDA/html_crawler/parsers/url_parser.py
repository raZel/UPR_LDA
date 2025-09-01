from UPR_LDA.models import  UPRCivilSocietyTags
from typing import Generic, List, Callable, Awaitable, Dict
import abc
import requests
import logging
from copy import deepcopy
from pydantic import BaseModel
from bs4 import BeautifulSoup
from typing import Self, Tuple
from UPR_LDA.html_crawler.session_manager import SessionManager
import time
import random

class MaxRetriesExceededException(Exception):
    pass

_logger = logging.getLogger(__file__)

class ParserState(UPRCivilSocietyTags):
    url: str

    def create_new_state(self, url: str):
        new_state =  deepcopy(self)
        new_state.url = url
        return new_state

class URLParser(abc.ABC):
    def __init__(self, session_manager: SessionManager) -> None:
        super().__init__()
        self._session_manager = session_manager

    @property
    def _session(self) -> requests.Session:
        return self._session_manager.get_session()

    def get_url(self, url: str, max_retries: int = 4, backoff_factor: float = 2.0) -> BeautifulSoup:
        _logger.info("get_url: %s", url)
        for attempt in range(max_retries):
            try:
                time.sleep(random.uniform(0.2, 0.8))
                response = self._session.get(url)
                response.raise_for_status()  # Raise an exception for bad status codes
                return BeautifulSoup(response.text, 'lxml')
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 403:
                    _logger.warning(f"Attempt {attempt + 1}: Received 403 Forbidden for {url}. Retrying...")
                    if attempt == max_retries // 2:
                        self._session_manager.recreate_session()
                    min_wait = backoff_factor * (2 ** attempt)
                    max_wait = backoff_factor * (2 ** (attempt + 1))

                    sleep_time = random.uniform(min_wait,max_wait)
                    time.sleep(sleep_time)
                else:
                    _logger.error(f"HTTP error {e.response.status_code} for {url}: {e}")
                    raise
            except requests.exceptions.RequestException as e:
                _logger.error(f"Request failed for {url}: {e}")
                raise
        _logger.error(f"Failed to fetch {url} after {max_retries} attempts.")
        raise MaxRetriesExceededException(f"Max retries exceeded for {url}")
    def get_and_fill(self, state: ParserState) -> List[ParserState]:
        _logger.info("get_and_fill for url: %s", state.url)
        content = self.get_url(state.url)
        return self.parse(soup_content=content, state=state)

    @abc.abstractmethod
    def parse(self, soup_content: BeautifulSoup, state: ParserState) -> List[ParserState]:
        pass