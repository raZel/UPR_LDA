from UPR_LDA.models import  UPRDocumentMetaData
from .parsers import *
from typing import Generic, List, Callable, Awaitable, Iterable
import cloudscraper
import logging



_logger = logging.getLogger(__file__)

def crawl_upr_for_civil_society_submissions(url: str) -> List[UPRDocumentMetaData]:
    with cloudscraper.session() as session:
        stages: Iterable[URLParser] = (
            DocumentationByCountryParser(session=session), 
            CountryCyclesParser(session=session), 
            CivilSocietySubmissionsParser(session=session),
            )
        states = [ParserState(url=url)]
        for stage in stages:
            stage_results = [stage.get_and_fill(state=state) for state in states]
            states = [state for state_list in stage_results for state in state_list]
    return [UPRDocumentMetaData(**state.model_dump()) for state in states]
