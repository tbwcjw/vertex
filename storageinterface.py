from abc import ABC, abstractmethod

class StorageInterface(ABC):
    @abstractmethod
    def get_seeder_count(self, info_hash):
        pass
    
    def get_leecher_count(self, info_hash):
        pass

    def get_peers(self, info_hash):
        pass

    def get_peers_for_response(self, info_hash, numwant):
        pass
    
    def insert_peer(self, peer_id, info_hash, ipv4, ipv6, port, uploaded, downloaded, left, last_event, is_complete):
        pass

    def update_peer(self, peer_id, info_hash, is_complete, last_event, uploaded, downloaded, left):
        pass

    def cleanup_peers(self):
        pass