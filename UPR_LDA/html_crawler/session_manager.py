import cloudscraper

import abc
import requests

class SessionManager(abc.ABC):
    @abc.abstractmethod
    def get_session(self) -> requests.Session:
        pass

    @abc.abstractmethod
    def recreate_session(self) -> None:
        pass


class CloudScraperSessionManager(SessionManager):
    def __init__(self):
        self._session = None

    def get_session(self):
        if self._session is None:
            self._session = cloudscraper.create_scraper()
        return self._session
    
    def recreate_session(self):
        if self._session:
            self._session.close()
        self._session = cloudscraper.create_scraper()
