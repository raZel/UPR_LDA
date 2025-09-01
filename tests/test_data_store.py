from UPR_LDA.data_store import JSONDataStore
from UPR_LDA.models import ModelKey, UPRDocumentMetaData
import tempfile
import logging
import os

logger = logging.Logger(__name__)

class TestDataStore:
    @staticmethod
    def create_upr_metadata(index: int) -> UPRDocumentMetaData:
        return UPRDocumentMetaData(
            key=f"key{index}",
            url=f"url{index}",
            country=f"country{index}",
            cycle=f"cycle{index}",
            organization_name=f"org{index}",
            continent=f"continent{index}",
        )

    def testJSONDataStore(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            json_file_name =  "json_data_store_test_data.json"
            json_path = os.path.join(tmpdir, json_file_name)
            store = JSONDataStore(model_cls=UPRDocumentMetaData, json_path=json_path)
            assert len(store.all()) == 0
            data = [self.create_upr_metadata(i) for i in range(3)]
            store.add(data[1])
            assert store.get("key1") == data[1]
            store.persist()
            store.add(data[0])
            assert store.get("key1") == data[1]
            assert store.get("key0") == data[0]
            store = JSONDataStore(model_cls=UPRDocumentMetaData,json_path=json_path)
            assert store.get("key1") == data[1]
            assert store.get("key0") is None
            with store.autoPersist:
                store.add(data[2])
            assert store.get("key0") is None            
            assert store.get("key1") == data[1]
            assert store.get("key2") == data[2]
            store = JSONDataStore(model_cls=UPRDocumentMetaData,json_path=json_path)
            assert store.get("key0") is None            
            assert store.get("key1") == data[1]
            assert store.get("key2") == data[2]
            




