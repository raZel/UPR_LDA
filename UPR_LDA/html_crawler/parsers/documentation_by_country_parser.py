from .url_parser import URLParser, ParserState
from typing import List
from bs4 import BeautifulSoup
from copy import copy
import re
from urllib.parse import urljoin

class DocumentationByCountryParser(URLParser):
    def parse(self, content: str, state: ParserState) -> List[ParserState]:
        soup = BeautifulSoup(content, 'lxml')
        country_links = soup.find_all('a', href=re.compile(r'/en/hr-bodies/upr/.*-index'))
        states = []
        for link in country_links:
            relative_url = link.get('href')
            if not relative_url:
                continue

            new_state = copy(state)
            # Convert the found relative URL to an absolute one for the next crawl stage
            new_state.url = urljoin(state.url, relative_url)
            new_state.tags.country = link.text.strip() # TODO: strip bad characters keep it ascii
            states.append(new_state)
        return states