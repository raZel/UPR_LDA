from typing import TypeVar, Generic, Type, List, Iterator, Dict, Optional
from pydantic import BaseModel
import csv
import os
from contextlib import contextmanager
from UPR_LDA.models import DocumentMetaData, ModelKey
from copy import deepcopy

T = TypeVar('T', bound=DocumentMetaData)
_KEY_FIELD_NAME = "key"
def get_document_key(val: DocumentMetaData) -> ModelKey:
    return getattr(val, _KEY_FIELD_NAME)

class CSVDataStore(Generic[T]):
    def __init__(self, model_cls: Type[T], csv_path: str):
        self.model_cls = model_cls
        self.csv_path = csv_path
        self.fieldnames = list(model_cls.model_fields.keys())
        self._data: Dict[ModelKey,T] = {}
        self._load()

    def _create_csv(self) -> None:
        with open(self.csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames)
            writer.writeheader()

    def _load(self) -> None:
        if not os.path.exists(self.csv_path):
            self._create_csv()

        with open(self.csv_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            self._data = {row[_KEY_FIELD_NAME] :self.model_cls(**row) for row in reader}

    def add(self, val: T) -> None:
        self._data[get_document_key(val)] = deepcopy(val)

    def all(self) -> List[T]:
        return deepcopy(list(self._data.values()))
    
    def get(self, key: ModelKey) -> Optional[T]:
        return deepcopy(self._data.get(key))

    def persist(self) -> None:
        with open(self.csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames)
            writer.writeheader()
            for item in sorted(self._data.values(), key=lambda x: get_document_key(x)):
                writer.writerow(item.model_dump())

    @property
    @contextmanager
    def autoPersist(self) -> Iterator[None]:
        try:
            yield
        finally:
            self.persist()
