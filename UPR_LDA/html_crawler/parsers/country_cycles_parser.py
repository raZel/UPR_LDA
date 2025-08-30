from .url_parser import URLParser, ParserState
from typing import List, NamedTuple, Iterator, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
from enum import Enum
from UPR_LDA.models import UPRCycle

class StakeholdersSummaryReference(NamedTuple):
    url: str
    cycle: UPRCycle


class CountryCyclesParser(URLParser):
    @staticmethod
    def find_cycle(title: str) -> Optional[UPRCycle]:
        return next((uc for uc in UPRCycle if uc.lower() in title.lower()), None)

    def find_stake_holders_summary_links(self, soup: BeautifulSoup, base_url: str) -> Iterator[StakeholdersSummaryReference]:
        upr_cycle_title_tags = soup.find_all(class_='upr-cycle-title')
        
        for cycle_title_tag in upr_cycle_title_tags:
            cycle = self.find_cycle(cycle_title_tag.text)
            if cycle is None or cycle in (UPRCycle.FOURTH,):
                continue
            
            strong_tag = next((t for t in cycle_title_tag.parent.find_all('strong') if 'Summary of stakeholders' in t.text),None)
            if strong_tag is None:
                continue
            ref_tag = strong_tag.find_next_sibling('a')
            if ref_tag is None:
                continue
            relative_url = ref_tag.get('href')
            if relative_url is None:
                continue
            
            absolute_url = urljoin(base_url, relative_url)
            yield StakeholdersSummaryReference(url=absolute_url, cycle=cycle)


    def parse(self, soup_content: BeautifulSoup, state: ParserState) -> List[ParserState]:
        new_states = []
        for ref in self.find_stake_holders_summary_links(soup_content, state.url):
            new_state = state.create_new_state(ref.url)
            new_state.tags.cycle = ref.cycle.value
            new_states.append(new_state)
        return new_states