from .url_parser import URLParser, ParserState
from typing import List
from bs4 import BeautifulSoup
import re
import logging
from urllib.parse import urljoin
from UPR_LDA.utils import clean_country_name

_logger = logging.getLogger(__name__)

class DocumentationByCountryParser(URLParser):
    def parse(self, soup_content: BeautifulSoup, state: ParserState) -> List[ParserState]:
        country_links = soup_content.find_all('a', href=re.compile(r'/en/hr-bodies/upr/.*-index'))
        _logger.info(f"Found {len(country_links)} country links on page {state.url}")
        new_states = []
        for link in country_links:
            relative_url = link.get('href')
            if not relative_url:
                _logger.warning("Found a country link tag with no href on page %s.", state.url)
                continue
            absolute_url = urljoin(state.url, relative_url)
            new_state = state.create_new_state(absolute_url)
            # Convert the found relative URL to an absolute one for the next crawl stage
            country_name = link.text.strip()
            new_state.country = clean_country_name(country_name)
            _logger.debug(f"Found country: {new_state.country} with url {new_state.url}")
            new_states.append(new_state)
        _logger.info(f"Parser created {len(new_states)} new states from page {state.url}.")
        return new_states