from UPR_LDA.models import  UPRDocumentMetaData
from .parsers import *
from typing import Generic, List, Callable, Awaitable, Iterable
import abc
import aiohttp
from bs4 import BeautifulSoup, Tag
import logging
from pydantic import BaseModel
import re
import copy
import asyncio


_logger = logging.getLogger(__file__)

async def crawl_upr_for_civil_society_submissions(url: str) -> List[UPRDocumentMetaData]:
    stages: Iterable[URLParser] = (DocumentationByCountryParser(),)
    states = [ParserState(url=url)]
    async with aiohttp.ClientSession() as session:
        for stage in stages:
            stage_tasks = [stage.get_and_fill(state=state, session=session) for state in states]
            stage_results = await asyncio.gather(*stage_tasks, return_exceptions=True)
            new_states = []
            for result in zip(states,stage_results):
                if isinstance(result[1],Exception):
                    _logger.error(f"Failed get and fill for {result[0]}. Exception={result[1]}")
                else:
                    new_states.append(result[1])
            states = new_states
    return [UPRDocumentMetaData(**state.model_dump()) for state in states]


