from abc import ABC, abstractmethod

class StorageInterface(ABC):
    @abstractmethod
    def get_seeder_count(self, info_hash):
        pass
    @abstractmethod
    def get_leecher_count(self, info_hash):
        pass
    @abstractmethod
    def get_peers(self, info_hash):
        pass
    @abstractmethod 
    def get_peers_for_response(self, info_hash, numwant):
        pass
    @abstractmethod
    def insert_peer(self, peer_id, info_hash, ipv4, ipv6, port, uploaded, downloaded, left, last_event, is_complete):
        pass
    @abstractmethod
    def update_peer(self, peer_id, info_hash, is_complete, last_event, uploaded, downloaded, left):
        pass
    @abstractmethod
    def cleanup_peers(self):
        pass
    @abstractmethod
    def fullscrape(self):
        pass
    @abstractmethod
    def is_duplicate(self):
        pass
    @abstractmethod
    def get_unique_infohash_count(self):
        pass
    @abstractmethod
    def get_all_peer_count(self):
        pass
    @abstractmethod
    def get_all_seeder_count(self):
        pass
    @abstractmethod
    def get_all_event_counts(self):
        pass
    @abstractmethod
    def get_all_leecher_count(self):
        pass