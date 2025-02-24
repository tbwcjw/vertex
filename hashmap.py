import time
from collections import defaultdict

from storageinterface import StorageInterface
from configloader import ConfigLoader

config = ConfigLoader()
CLEANUP_TIME = config.get('storage.remove_older_than_secs')  


class Hashmap(StorageInterface):
    def __init__(self):
        self.peers = {}  
        self.info_hash_index = defaultdict(set)  

    def insert_peer(self, peer_id, info_hash, ipv4, ipv6, port, uploaded, downloaded, left, last_event, is_complete):
        peer_key = (peer_id, info_hash)
        peer_data = {
            "peer_id": peer_id,
            "info_hash": info_hash,
            "ip": ipv4 if ipv4 else ipv6,
            "port": port,
            "uploaded": uploaded,
            "downloaded": downloaded,
            "left": left,
            "last_event": last_event,
            "is_completed": is_complete,
            "last_updated": time.time(),  
        }
        self.peers[peer_key] = peer_data
        self.info_hash_index[info_hash].add(peer_id)

    def update_peer(self, peer_id, info_hash, is_complete, last_event, uploaded, downloaded, left):
        peer_key = (peer_id, info_hash)
        if peer_key in self.peers:
            self.peers[peer_key].update({
                "is_completed": is_complete,
                "last_event": last_event,
                "uploaded": uploaded,
                "downloaded": downloaded,
                "left": left,
                "last_updated": time.time(),
            })

    def get_seeder_count(self, info_hash):
        return sum(1 for peer in self.peers.values() if peer["info_hash"] == info_hash and peer["is_completed"])

    def get_leecher_count(self, info_hash):
        return sum(1 for peer in self.peers.values() if peer["info_hash"] == info_hash and not peer["is_completed"])

    def get_peers(self, info_hash):
        return [peer for peer in self.peers.values() if peer["info_hash"] == info_hash]

    def get_peers_for_response(self, info_hash, numwant):
        peers = {
            peer["peer_id"]: {"ip": peer["ip"], "port": peer["port"]}
            for peer in self.peers.values() if peer["info_hash"] == info_hash
        }
        return dict(list(peers.items())[:numwant])

    def cleanup_peers(self):
        current_time = time.time()
        removed_count = 0
        to_remove = [
            key for key, peer in self.peers.items()
            if current_time - peer["last_updated"] > CLEANUP_TIME
        ]

        for key in to_remove:
            info_hash = self.peers[key]["info_hash"]
            self.info_hash_index[info_hash].discard(key[0]) 
            del self.peers[key]
            removed_count += 1

        return {"deleted_peers": removed_count}
