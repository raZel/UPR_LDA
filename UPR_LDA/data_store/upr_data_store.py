from typing import List, Callable, Iterable
from .data_store import JSONDataStore
from UPR_LDA.models import UPRDocumentMetaData, UPRCycle


class UPRDocumentMetaDataFiltersMixin:
    """A mixin for JSONDataStore to add UPRDocumentMetaData specific filters."""

    # This is a forward declaration for type checkers to know about the filter method from JSONDataStore.
    def filter(self, predicate: Callable[[UPRDocumentMetaData], bool]) -> List[UPRDocumentMetaData]:
        ...

    def filter_by_cycle(self, cycles: Iterable[UPRCycle]) -> List[UPRDocumentMetaData]:
        """Filters documents by UPR cycles."""
        return self.filter(lambda doc: doc.cycle is not None and doc.cycle in [c.value for c in cycles])

    def filter_by_country(self, countries: Iterable[str]) -> List[UPRDocumentMetaData]:
        """Filters documents by country name (case-insensitive) from a list of countries."""
        return self.filter(lambda doc: doc.country is not None and any(country.lower() in doc.country.lower() for country in countries))


class UPRDataStore(JSONDataStore[UPRDocumentMetaData], UPRDocumentMetaDataFiltersMixin):
    """
    A specialized data store for UPRDocumentMetaData with convenience filter methods.
    """
    def __init__(self, json_path: str):
        super().__init__(model_cls=UPRDocumentMetaData, json_path=json_path)