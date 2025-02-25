from database import Database
from hashmap import Hashmap

class StorageManager:
    _instance = None

    def __new__(cls, storage_type="sqlite"):
        if cls._instance is None:
            cls._instance = super(StorageManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, storage_type="sqlite"):
        if not self._initialized:
            print(f"StorageManager: set type {storage_type}")
            self.set_storage(storage_type)
            self._initialized = True  # Ensures init runs only once

    def set_storage(self, storage_type):
        if storage_type == "sqlite":
            self.storage = Database()
        elif storage_type == "hashmap":
            self.storage = Hashmap()
        else:
            raise NotImplementedError("Storage type not implemented")
        
    def __getattr__(self, name):
        return getattr(self.storage, name)  
