from UPR_LDA.models import  UPRDocumentMetaData
from .parsers import *
from typing import Generic, List, Callable, Awaitable, Iterable
import requests
import logging

import copy
import asyncio


_logger = logging.getLogger(__file__)

def crawl_upr_for_civil_society_submissions(url: str) -> List[UPRDocumentMetaData]:
    stages: Iterable[URLParser] = (DocumentationByCountryParser(),)
    states = [ParserState(url=url)]
    with requests.Session() as session:
        for stage in stages:
            stage_results = [stage.get_and_fill(state=state, session=session) for state in states]
            new_states = []
            for result in stage_results:
                new_states.append(result)
            states = new_states
    return [UPRDocumentMetaData(**state.model_dump()) for state in states]
