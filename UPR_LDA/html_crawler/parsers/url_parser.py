from UPR_LDA.models import  UPRCivilSocietyTags
from typing import Generic, List, Callable, Awaitable, Dict
import abc
import requests
import logging
from pydantic import BaseModel

_logger = logging.getLogger(__file__)

class ParserState(BaseModel):
    url: str
    tags: UPRCivilSocietyTags = UPRCivilSocietyTags()

class URLParser(abc.ABC):
    def __init__(self) -> None:
        super().__init__()
    
    def get_and_fill(self, state: ParserState, session: requests.Session, max_retries: int = 3) -> List[ParserState]:
        _logger.info("get_and_fill for url: %s", state.url)
        response = session.get(state.url)
        response.raise_for_status()  # Raise an exception for bad status codes
        content = response.text
        return self.parse(content=content, state=state)

    @abc.abstractmethod
    def parse(self, content: str, state: ParserState) -> List[ParserState]:
        pass
