from UPR_LDA.data_store import CSVDataStore
from UPR_LDA.models import ModelKey, UPRDocumentMetaData
import tempfile
import logging
import os

logger = logging.Logger(__name__)

class TestDataStore:
    def testCSVDataStore(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_file_name =  "csv_data_store_test_data.csv"
            csv_path = os.path.join(tmpdir, csv_file_name)
            store = CSVDataStore(model_cls=UPRDocumentMetaData, csv_path=csv_path)
            assert len(store.all()) == 0
            fields = list(UPRDocumentMetaData.model_fields.keys())
            data = [UPRDocumentMetaData(**{k:k+str(i) for k in fields}) for i in range(3)]
            store.add(data[1])
            assert store.get("key1") == data[1]
            store.persist()
            store.add(data[0])
            assert store.get("key1") == data[1]
            assert store.get("key0") == data[0]
            store = CSVDataStore(model_cls=UPRDocumentMetaData,csv_path=csv_path)
            assert store.get("key1") == data[1]
            assert store.get("key0") is None
            with store.autoPersist:
                store.add(data[2])
            assert store.get("key0") is None            
            assert store.get("key1") == data[1]
            assert store.get("key2") == data[2]
            store = CSVDataStore(model_cls=UPRDocumentMetaData,csv_path=csv_path)
            assert store.get("key0") is None            
            assert store.get("key1") == data[1]
            assert store.get("key2") == data[2]
            




