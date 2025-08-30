from UPR_LDA.models import  UPRCivilSocietyTags
from typing import Generic, List, Callable, Awaitable, Dict
import abc
import requests
import logging
from copy import deepcopy
from pydantic import BaseModel
from bs4 import BeautifulSoup
from typing import Self

_logger = logging.getLogger(__file__)

class ParserState(BaseModel):
    url: str
    tags: UPRCivilSocietyTags = UPRCivilSocietyTags()

    def create_new_state(self, url: str):
        new_state =  deepcopy(self)
        new_state.url = url
        return new_state

class URLParser(abc.ABC):
    def __init__(self, session: requests.Session) -> None:
        super().__init__()
        self._session = session

    def get_url(self, url: str) -> BeautifulSoup:
        _logger.info("get_url: %s", url)
        response = self._session.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        return BeautifulSoup(response.text, 'lxml')

    def get_and_fill(self, state: ParserState) -> List[ParserState]:
        _logger.info("get_and_fill for url: %s", state.url)
        content = self.get_url(state.url)
        return self.parse(soup_content=content, state=state)

    @abc.abstractmethod
    def parse(self, soup_content: BeautifulSoup, state: ParserState) -> List[ParserState]:
        pass