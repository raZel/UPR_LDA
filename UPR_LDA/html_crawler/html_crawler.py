from UPR_LDA.models import  UPRDocumentMetaData
from .parsers import *
from typing import Generic, List, Callable, Awaitable, Iterable, Optional
import logging
from UPR_LDA.html_crawler.session_manager import CloudScraperSessionManager
import time
from UPR_LDA.data_store import UPRDataStore

_logger = logging.getLogger(__file__)

def crawl_upr_for_civil_society_submissions(url: str, data_store: UPRDataStore):
    session_manager = CloudScraperSessionManager()
    countries_states = DocumentationByCountryParser(session_manager=session_manager).get_and_fill(ParserState(url=url))
    existing_countries = {doc.country for doc in data_store.all()}
    _logger.info("Skipping existing countries: %s", existing_countries)
    countries_to_scrape = [s for s in countries_states if s.country not in existing_countries]

    stages: Iterable[URLParser] = ( 
        CountryCyclesParser(session_manager=session_manager), 
        CivilSocietySubmissionsParser(session_manager=session_manager),
        )
    for country_state in countries_to_scrape:
        states = [country_state]
        _logger.info("Start scraping country: %s", country_state.country)
        for stage in stages:
            stage_results = []
            retry_states = []
            for state in states:
                try:
                    results = stage.get_and_fill(state=state)
                    stage_results.extend(results)
                except MaxRetriesExceededException:
                    _logger.warning("max retries for state: %s", state)
                    retry_states.append(state)
            
            if len(retry_states):
                _logger.info("sleeping for 20 seconds before retrying failed states")
                time.sleep(20)
                for state in retry_states: # type: ignore
                    results = stage.get_and_fill(state=state)
                    stage_results.extend(results)

            states = stage_results
        _logger.info("Finished scraping country: %s, found %s documents", country_state.country, len(states))
        results = [UPRDocumentMetaData(**state.model_dump()) for state in states]
        with data_store.autoPersist:
            for res in results:
                data_store.add(res)
        
