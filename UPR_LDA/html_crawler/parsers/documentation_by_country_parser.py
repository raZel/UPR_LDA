from .url_parser import URLParser, ParserState
from typing import List
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
from UPR_LDA.utils import clean_country_name

class DocumentationByCountryParser(URLParser):
    def parse(self, soup_content: BeautifulSoup, state: ParserState) -> List[ParserState]:
        country_links = soup_content.find_all('a', href=re.compile(r'/en/hr-bodies/upr/.*-index'))
        new_states = []
        for link in country_links:
            relative_url = link.get('href')
            if not relative_url:
                continue
            new_state = state.create_new_state(urljoin(state.url, relative_url))
            # Convert the found relative URL to an absolute one for the next crawl stage
            country_name = link.text.strip()
            new_state.tags.country = clean_country_name(country_name)
            new_states.append(new_state)
            break
        return new_states