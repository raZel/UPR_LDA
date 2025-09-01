from .url_parser import URLParser, ParserState
from typing import List, NamedTuple, Iterator, Optional, Tuple, Iterable
from bs4 import BeautifulSoup
from bs4.element import PageElement
from urllib.parse import urljoin
import re
import logging
from enum import Enum

_logger = logging.getLogger(__name__)

class HeadersLocation(NamedTuple):
    org_name: int
    languages: int

class CivilSocietySubmissionReference(NamedTuple):
    doc_url: str
    org_name: str

class CivilSocietySubmissionsParser(URLParser): 
    
    def find_civil_society_table(self, soup: BeautifulSoup, base_url: str) -> Tuple[Optional[PageElement], str]:
        _logger.debug(f"Searching for civil society table on page {base_url}")
        table = next((t for t in soup.find_all('table') \
                     if 'civil society' in t.get_text().lower() \
                     or 'civil society' in t.get('summary', '').lower()), None)
        if table is not None:
            _logger.debug("Found civil society table directly on page.")
            return table, base_url
        
        # If table not found directly, try to find it within an iframe
        _logger.debug("Civil society table not found directly, searching in iframe.")
        main_tag = soup.find('main')
        if main_tag is None:
            _logger.warning(f"Could not find <main> tag on page {base_url}")
            return None, base_url
        iframe_tag = main_tag.find('iframe')
        if iframe_tag is None:
            _logger.warning(f"Could not find <iframe> in <main> on page {base_url}")
            return None, base_url
        iframe_src = iframe_tag.get('src')
        if iframe_src is None:
            _logger.warning(f"Found <iframe> but it has no 'src' on page {base_url}")
            return None, base_url
        
        iframe_base_url = urljoin(base_url, iframe_src)
        _logger.debug(f"Found iframe with src: {iframe_src}. Fetching content from {iframe_base_url}.")
        iframe_soup = self.get_url(iframe_base_url)
        table = next((t for t in iframe_soup.find_all('table') \
                     if 'civil society' in t.get_text().lower() \
                     or 'civil society' in t.get('summary', '').lower()), None)
        if table:
            _logger.debug(f"Found civil society table inside iframe from {iframe_base_url}.")
        else:
            _logger.warning(f"Could not find civil society table inside iframe from {iframe_base_url}")
        return table, iframe_base_url

        
    @staticmethod
    def search_for_headers(headers: Iterable[str]) -> HeadersLocation:
        org_name_col_idx = -1
        languages_col_idx = -1

        for i, header in enumerate(headers):
            if 'organisation name' in header.lower() or 'name of organisation' in header.lower():
                org_name_col_idx = i
            elif 'languages' in header.lower():
                languages_col_idx = i
            if org_name_col_idx != -1 and languages_col_idx != -1:
                break
        
        if org_name_col_idx == -1:
            _logger.warning("Could not find 'Organisation Name' header in %s.", headers)
        if languages_col_idx == -1:
            _logger.warning("Could not find 'Languages' header in %s.", headers)

        return HeadersLocation(org_name=org_name_col_idx, languages=languages_col_idx)

    
    def find_civil_society_submissions(self, soup: BeautifulSoup, base_url: str) -> Iterator[CivilSocietySubmissionReference]:

        table, current_base_url = self.find_civil_society_table(soup=soup, base_url=base_url)
        if table is None:
            _logger.error(f"Could not find civil society submissions table on {base_url}")
            return
        
        rows = table.find_all('tr') # type: ignore
        if not rows:
            _logger.warning(f"Civil society table found on {base_url}, but it has no rows.")
            return

        header_row = rows[0]
        data_rows = rows[1:]

        headers = [th.get_text(strip=True) for th in header_row.find_all('th')]
        org_name_col_idx, languages_col_idx = self.search_for_headers(headers=headers)
        if org_name_col_idx == -1 or languages_col_idx == -1:
            _logger.error(f"Required columns ('Organisation Name', 'Languages') not found in table on {base_url}. Headers found: {headers}, Fallback")
            # Fallback if headers are not in <th>, assume first row <td> are headers
            header_row = data_rows[0]
            data_rows = data_rows[1:]
            headers = [td.get_text(strip=True) for td in header_row.find_all('td')]

        org_name_col_idx, languages_col_idx = self.search_for_headers(headers=headers)
        if org_name_col_idx == -1 or languages_col_idx == -1:
            _logger.error(f"Required columns ('Organisation Name', 'Languages') not found in table on {base_url}. Headers found: {headers}")
            return

        _logger.debug(f"Found {len(data_rows)} data rows in civil society table.")
        for row in data_rows:
            cols = row.find_all('td')
            if len(cols) > max(org_name_col_idx, languages_col_idx):
                org_name_tag = cols[org_name_col_idx]
                languages_tag = cols[languages_col_idx]

                org_name = org_name_tag.get_text(strip=True)
                
                # Find all 'a' tags within the languages column that contain 'E' (for English documents)
                english_links_found = 0
                for link_tag in languages_tag.find_all('a', href=True):
                    if link_tag.get_text(strip=True).lower() in ('e', 'english'): # Assuming 'E' indicates English document
                        relative_url = link_tag.get('href')
                        if relative_url is None:
                            _logger.warning(f"Found English document link with no href for org '{org_name}'")
                            continue
                        absolute_url = urljoin(current_base_url, relative_url)
                        _logger.debug(f"Found submission for '{org_name}': {absolute_url}")
                        yield CivilSocietySubmissionReference(doc_url=absolute_url, org_name=org_name)
                        english_links_found += 1
                if english_links_found == 0:
                    _logger.debug(f"No English document link found for org '{org_name}'")
            else:
                _logger.warning(f"Row has fewer columns than expected. Skipping. Row content: {[c.get_text(strip=True) for c in cols]}")

    def parse(self, soup_content: BeautifulSoup, state: ParserState) -> List[ParserState]:
        new_states = []
        submission_count = 0
        _logger.info(f"searching submissions for {state.country} cycle {state.cycle}")
        for ref in self.find_civil_society_submissions(soup_content, state.url):
            new_state = state.create_new_state(ref.doc_url)
            new_state.organization_name = ref.org_name
            new_states.append(new_state)
            submission_count += 1
        _logger.info(f"Found {submission_count} civil society submissions on page {state.url}.")
        return new_states