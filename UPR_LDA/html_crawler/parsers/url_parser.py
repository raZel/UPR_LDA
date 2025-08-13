from UPR_LDA.models import  UPRCivilSocietyTags
from typing import Generic, List, Callable, Awaitable
import abc
import aiohttp
from bs4 import BeautifulSoup, Tag
import logging
from pydantic import BaseModel
import re
import copy


_logger = logging.getLogger(__file__)

class ParserState(BaseModel):
    url: str
    tags: UPRCivilSocietyTags = UPRCivilSocietyTags()

class URLParser(abc.ABC):
    def __init__(self) -> None:
        super().__init__()
    
    async def get_and_fill(self, state: ParserState, session: aiohttp.ClientSession) -> List[ParserState]:
        async with session.get(state.url) as response:
            try:
                response.raise_for_status() # Raise an exception for bad status codes
                content =  await response.text()
                return self.parse(content=content, state=state)
            except aiohttp.ClientResponseError:
                _logger.error(f"Request to {state.url} failed with status {response.status}. Response: {await response.text()}")
                raise
                

    @abc.abstractmethod
    def parse(self, content: str, state: ParserState) -> List[ParserState]:
        pass
