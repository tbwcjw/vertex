from itertools import islice
import time
from collections import defaultdict

from storageinterface import StorageInterface
from configloader import ConfigLoader

config = ConfigLoader()

class Hashmap(StorageInterface):
    def __init__(self):
        self.peers = {}  
        self.info_hash_index = defaultdict(set)  
        self.cleanup_time = config.get('storage.remove_older_than_secs')  

    def insert_peer(self, peer_id, no_peer_id, info_hash, ipv4, ipv6, port, uploaded, downloaded, left, last_event, is_complete):
        peer_key = (peer_id, info_hash)
        peer_data = {
            "peer_id": peer_id,
            "no_peer_id": no_peer_id,
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
        print("INFO HASH INDEX " + dict(self.info_hash_index).__str__())

    def get_unique_infohash_count(self):
        return len(self.info_hash_index)
    
    def get_all_peer_count(self):
        return len(self.peers)

    def get_all_seeder_count(self):
        return sum(1 for peer in self.peers.values() if peer["is_completed"] and peer["last_event"] != "stopped")

    def get_all_leecher_count(self):
        return sum(1 for peer in self.peers.values() if not peer["is_completed"] and peer["last_event"] != "stopped")

    def get_all_event_counts(self):
        event_counts = defaultdict(int)
        for peer in self.peers.values():
            if peer["last_event"] in ("started", "stopped", "completed"):
                event_counts[peer["last_event"]] += 1
        return dict(event_counts)

    def update_peer(self, peer_id, no_peer_id, info_hash, is_complete, last_event, uploaded, downloaded, left):
        peer_key = (peer_id, info_hash)
        if peer_key in self.peers:
            self.peers[peer_key].update({
                "no_peer_id": no_peer_id,
                "is_completed": is_complete,
                "last_event": last_event,
                "uploaded": uploaded,
                "downloaded": downloaded,
                "left": left,
                "last_updated": time.time(),
            })

    def get_seeder_count(self, info_hash):
        return sum(1 for peer in self.peers.values() if peer["info_hash"] == info_hash and peer["is_completed"])

    def is_duplicate(self, peer_id, info_hash):
        return (peer_id, info_hash) in self.peers

    def get_leecher_count(self, info_hash):
        return sum(1 for peer in self.peers.values() if peer["info_hash"] == info_hash and not peer["is_completed"])

    def get_peers(self, info_hash):
        print(len(self.peers))
        return [peer for peer in self.peers.values() if peer["info_hash"] == info_hash]

    def fullscrape(self):
        return [peer['info_hash'] for peer in self.peers.values()]
    
    def get_peers_for_response(self, info_hash, numwant, peer_id):
        peers = {
            (peer["peer_id"] if not peer.get("no_peer_id", 0) else f"anonymous_{index}"): 
            {"ip": peer["ip"], "port": peer["port"]}
            for index, peer in enumerate(self.peers.values()) 
            if peer["info_hash"] == info_hash and peer["peer_id"] != peer_id
        }
        return dict(islice(peers.items(), numwant))

    def cleanup_peers(self):
        current_time = time.time()
        removed_count = 0
        to_remove = [
            key for key, peer in self.peers.items()
            if current_time - peer["last_updated"] > self.cleanup_time
        ]

        for key in to_remove:
            info_hash = self.peers[key]["info_hash"]
            self.info_hash_index[info_hash].discard(key[0]) 
            del self.peers[key]
            removed_count += 1

        return {"deleted_peers": removed_count}

#singleton instance
hashmap_instance = Hashmap()