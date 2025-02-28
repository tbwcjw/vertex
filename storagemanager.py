from database import sqlite_instance
from hashmap import hashmap_instance
from log import LogLevel

class StorageManager:
    _instance = None

    def __new__(cls, storage_type="sqlite"):
        if cls._instance is None:
            cls._instance = super(StorageManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, storage_type="sqlite"):
        if not self._initialized:
            print(f"StorageManager: set type {storage_type}", log_level=LogLevel.INFO)
            self.set_storage(storage_type)
            self._initialized = True 

    def set_storage(self, storage_type):
        if storage_type == "sqlite":
            self.storage = sqlite_instance
        elif storage_type == "hashmap":
            self.storage = hashmap_instance
        else:
            print(f"storage type `{storage_type}` not implemented", log_level=LogLevel.CRITICAL)
        
    def __getattr__(self, name):
        return getattr(self.storage, name)  
