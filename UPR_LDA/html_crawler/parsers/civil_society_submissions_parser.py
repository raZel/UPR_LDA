from .url_parser import URLParser, ParserState
from typing import List, NamedTuple, Iterator, Optional, Tuple, Iterable
from bs4 import BeautifulSoup
from bs4.element import PageElement
from urllib.parse import urljoin
import re
from enum import Enum

class HeadersLocation(NamedTuple):
    org_name: int
    languages: int

class CivilSocietySubmissionReference(NamedTuple):
    doc_url: str
    org_name: str

class CivilSocietySubmissionsParser(URLParser):
    
    def find_civil_society_table(self, soup: BeautifulSoup, base_url: str) -> Optional[PageElement]:
        table = next((t for t in soup.find_all('table') \
                     if 'civil society' in t.get_text().lower() \
                     or 'civil society' in t.get('summary').lower()), None)
        if table is not None:
            return table
        
        #find the iframe:
        main = soup.find('main')
        if main is None:
            return None
        iframe = main.find('iframe')
        if iframe is None:
            return None
        src = iframe.get('src')
        if src is None:
            return None
        soup = self.get_url(src)
        return next((t for t in soup.find_all('table') \
                     if 'civil society' in t.get_text().lower() \
                     or 'civil society' in t.get('summary').lower()), None)

        
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
        return HeadersLocation(org_name=org_name_col_idx, languages=languages_col_idx)

    
    def find_civil_society_submissions(self, soup: BeautifulSoup, base_url: str) -> Iterator[CivilSocietySubmissionReference]:

        table = self.find_civil_society_table(soup=soup, base_url=base_url)
        if table is None:
            return
        
        rows = table.find_all('tr')
        if not rows:
            return

        header_row = rows[0]
        headers = [th.get_text(strip=True) for th in header_row.find_all('th')]
        org_name_col_idx, languages_col_idx = self.search_for_headers(headers=headers)
        if org_name_col_idx == -1 or languages_col_idx == -1:
            # Fallback if headers are not in <th>, assume first row <td> are headers
            headers = [td.get_text(strip=True) for td in header_row.find_all('td')]
            rows = rows[1:]

        org_name_col_idx, languages_col_idx = self.search_for_headers(headers=headers)
        if org_name_col_idx == -1 or languages_col_idx == -1:
            return # Required columns not found

        for row in rows: # Skip header row
            cols = row.find_all('td')
            if len(cols) > max(org_name_col_idx, languages_col_idx):
                org_name_tag = cols[org_name_col_idx]
                languages_tag = cols[languages_col_idx]

                org_name = org_name_tag.get_text(strip=True)
                
                # Find all 'a' tags within the languages column that contain 'E' (for English documents)
                for link_tag in languages_tag.find_all('a', href=True):
                    if 'E' in link_tag.get_text(strip=True): # Assuming 'E' indicates English document
                        relative_url = link_tag.get('href')
                        if relative_url is None:
                            continue
                        absolute_url = urljoin(base_url, relative_url)
                        yield CivilSocietySubmissionReference(doc_url=absolute_url, org_name=org_name)

    def parse(self, soup_content: BeautifulSoup, state: ParserState) -> List[ParserState]:
        new_states = []
        for ref in self.find_civil_society_submissions(soup_content, state.url):
            new_state = state.create_new_state(ref.doc_url)
            new_state.tags.organization_name = ref.org_name
            new_states.append(new_state)
        return new_states