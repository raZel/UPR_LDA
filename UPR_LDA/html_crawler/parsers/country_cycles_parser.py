from .url_parser import URLParser, ParserState
from typing import List, NamedTuple, Iterator, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import logging
from enum import Enum
from UPR_LDA.models import UPRCycle

_logger = logging.getLogger(__name__)

class StakeholdersSummaryReference(NamedTuple):
    url: str
    cycle: UPRCycle


class CountryCyclesParser(URLParser):
    @staticmethod
    def find_cycle(title: str) -> Optional[UPRCycle]:
        if 'thrid' in title.lower():
            title = 'Third'
        return next((uc for uc in UPRCycle if uc.lower() in title.lower()), None)

    def find_stake_holders_summary_links(self, soup: BeautifulSoup, base_url: str) -> Iterator[StakeholdersSummaryReference]:
        upr_cycle_title_tags = soup.find_all(class_='upr-cycle-title')
        _logger.debug(f"Found {len(upr_cycle_title_tags)} cycle title tags on page {base_url}")
        if len(upr_cycle_title_tags) == 0:
            _logger.debug(f"Falling back to searching h2 headers")
            
            upr_cycle_title_tags = [t for t in soup.find_all('h2') if 'ycle' in t.text.lower()]
            _logger.debug(f"Found {len(upr_cycle_title_tags)} cycle title tags on page {base_url}")

        
        for cycle_title_tag in upr_cycle_title_tags:
            cycle = self.find_cycle(cycle_title_tag.text)
            if cycle is None:
                _logger.debug(f"Could not determine cycle from title: '{cycle_title_tag.text}'")
                continue
            
            if cycle in (UPRCycle.FOURTH,):
                _logger.debug(f"Skipping cycle {cycle.value} as it is not currently supported.")
                continue
            
            strong_tag = next((t for t in cycle_title_tag.parent.find_all('strong') if 'summary of stakeholders' in t.text.lower()),None)
            if strong_tag is None:
                _logger.debug(f"Not found, Searching 3 parents up for 'Summary of stakeholders' strong tag found for cycle {cycle.value} on page {base_url}")
                strong_tag = next((t for t in cycle_title_tag.parent.parent.parent.find_all('strong') if 'summary of stakeholders' in t.text.lower()),None)
                if strong_tag is None:
                    _logger.debug(f"Not found, Searching 4 parents up for 'Summary of stakeholders' strong tag found for cycle {cycle.value} on page {base_url}")
                    strong_tag = next((t for t in cycle_title_tag.parent.parent.parent.parent.find_all('strong') if 'summary of stakeholders' in t.text.lower()),None)
            if strong_tag is None:
                _logger.debug(f"No 'Summary of stakeholders' strong tag found for cycle {cycle.value} on page {base_url}")
                continue

            ref_tag = strong_tag.find_next_sibling('a')
            if ref_tag is None:
                _logger.debug(f"No 'a' tag found next to 'Summary of stakeholders' for cycle {cycle.value} on page {base_url}")
                ref_tag = strong_tag.find('a')
            if ref_tag is None:
                continue
            relative_url = ref_tag.get('href')
            if relative_url is None:
                _logger.warning(f"Found 'a' tag with no href for cycle {cycle.value} on page {base_url}")
                continue
            
            absolute_url = urljoin(base_url, relative_url)
            _logger.debug(f"Found stakeholders summary link for cycle {cycle.value}: {absolute_url}")
            yield StakeholdersSummaryReference(url=absolute_url, cycle=cycle)


    def parse(self, soup_content: BeautifulSoup, state: ParserState) -> List[ParserState]:
        new_states = []
        for ref in self.find_stake_holders_summary_links(soup_content, state.url):
            new_state = state.create_new_state(ref.url)
            new_state.cycle = ref.cycle.value
            _logger.debug(f"Created new state for country {state.country}, cycle {new_state.cycle}, url {new_state.url}")
            new_states.append(new_state)
        _logger.info(f"Parser created {len(new_states)} new states from page {state.url}.")
        return new_states