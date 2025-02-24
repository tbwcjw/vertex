from database import Database
from hashmap import Hashmap

class StorageManager:
    def __init__(self, storage_type="sqlite"):
        print(f"StorageManager: set type {storage_type}")
        self.set_storage(storage_type)

    def set_storage(self, storage_type):
        if storage_type == "sqlite":
            self.storage = Database()
        elif storage_type == "hashmap":
            self.storage = Hashmap()
        else:
            raise NotImplementedError("Storage type not implemented")
        
    def __getattr__(self, name):
        return getattr(self.storage, name)