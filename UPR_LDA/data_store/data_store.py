from typing import TypeVar, Generic, Type, List, Iterator, Dict, Optional, Callable
from pydantic import BaseModel
import json
import os
from contextlib import contextmanager
from UPR_LDA.models import DocumentMetaData, ModelKey
from copy import deepcopy
from uuid import uuid4

T = TypeVar('T', bound=DocumentMetaData)
_KEY_FIELD_NAME = "key"
def get_document_key(val: DocumentMetaData) -> ModelKey:
    return getattr(val, _KEY_FIELD_NAME)

def set_document_key(val: DocumentMetaData, key: ModelKey):
    setattr(val, _KEY_FIELD_NAME, key)

class JSONDataStore(Generic[T]):
    def __init__(self, model_cls: Type[T], json_path: str):
        self.model_cls = model_cls
        self.json_path = json_path
        self._data: Dict[ModelKey,T] = {}
        self._load()

    def _create_json(self) -> None:
        # Ensure the directory for the JSON file exists
        os.makedirs(os.path.dirname(self.json_path), exist_ok=True)
        with open(self.json_path, 'w', newline='') as f:
            json.dump({}, f)

    def _load(self) -> None:
        if not os.path.exists(self.json_path):
            self._create_json()

        with open(self.json_path, 'r', newline='') as f:
            data = json.load(f)
            self._data = {o[_KEY_FIELD_NAME] :self.model_cls(**o) for o in data.get('data', [])}

    def add(self, val: T) -> None:
        if get_document_key(val) is None:
            set_document_key(val, str(uuid4()))
        self._data[get_document_key(val)] = deepcopy(val)

    def all(self) -> List[T]:
        return deepcopy(list(self._data.values()))
    
    def get(self, key: ModelKey) -> Optional[T]:
        return deepcopy(self._data.get(key))
    
    def filter(self, predicate: Callable[[T], bool]) -> List[T]:
        return [deepcopy(item) for item in self._data.values() if predicate(item)]
    
    def persist(self) -> None:
        with open(self.json_path, 'w', newline='') as f:
            to_dump = {"data": [d.model_dump() for d in sorted(self._data.values(), key=lambda x: get_document_key(x))]}
            json.dump(to_dump, f)

    @property
    @contextmanager
    def autoPersist(self) -> Iterator[None]:
        try:
            yield
        finally:
            self.persist()
