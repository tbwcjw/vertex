import socket
import struct
import random
import threading

from storagemanager import StorageManager
from configloader import ConfigLoader
from bencoding import Bencoding

# Load Config
config = ConfigLoader()
db = StorageManager(config.get('storage.type'))
bc = Bencoding()

# Constants
MAGIC_CONN_ID = 0x41727101980  # Protocol magic number
ACTION_CONNECT = 0
ACTION_ANNOUNCE = 1
ACTION_SCRAPE = 2
ACTION_ERROR = 3

EVENT_NONE = 0
EVENT_COMPLETED = 1
EVENT_STARTED = 2
EVENT_STOPPED = 3

INTERVAL = config.get('tracker.interval')
MIN_INTERVAL = config.get('tracker.min_interval')
TRACKER_ID = config.get('tracker.tracker_id')
MAX_NUM_WANT = config.get('tracker.max_num_want')

class UDPTracker:
    def __init__(self, ipv4_ip="127.0.0.1", ipv4_port=6970, ipv6_ip="::", ipv6_port=6971):
        self.sockets = []
        if config.get('udp.ipv4_enable'):
            self.server_ipv4 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.server_ipv4.bind((ipv4_ip, ipv4_port))
            print(f"UDP Tracker started on IPv4: {ipv4_ip}:{ipv4_port}")
            self.sockets.append(self.server_ipv4)

        if config.get('udp.ipv6_enable'):
            self.server_ipv6 = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
            self.server_ipv6.bind((ipv6_ip, ipv6_port))
            print(f"UDP Tracker started on IPv6: {ipv6_ip}:{ipv6_port}")
            self.sockets.append(self.server_ipv6)

    def run(self):
        threads = []
        for sock in self.sockets:
            thread_name = "tracker_udp_ipv6" if sock.family == socket.AF_INET6 else "tracker_udp_ipv4"
            thread = threading.Thread(target=self.listen, args=(sock,), name=thread_name)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

    def listen(self, sock):
        while True:
            data, addr = sock.recvfrom(1024)
            self.handle_packet(data, addr, sock.family)

    def send_error(self, transaction_id, addr, error_message):
        error_message_bytes = error_message.encode()
        response = struct.pack("!II", ACTION_ERROR, transaction_id) + error_message_bytes
        sock = self.server_ipv6 if addr[0].count(":") else self.server_ipv4
        sock.sendto(response, addr)


    def handle_packet(self, data, addr, family):
        if len(data) < 16:
            print(f"invalid packet from {addr}")
            return  # Ignore invalid packets

        action, = struct.unpack_from(">I", data, 8)
        is_ipv6 = family == socket.AF_INET6
        
        if action == ACTION_CONNECT:
            self.handle_connect(data, addr, is_ipv6)
        elif action == ACTION_ANNOUNCE:
            self.handle_announce(data, addr, is_ipv6)
        elif action == ACTION_SCRAPE:
            self.handle_scrape(data, addr, is_ipv6)

    def handle_connect(self, data, addr, is_ipv6):
        print(f"connection {addr}: {data.hex()}")
        if len(data) < 16:
            self.send_error(0, addr, "Invalid packet size for connect request.")
            return
        transaction_id = struct.unpack_from(">I", data, 12)[0]
        protocol_id = struct.unpack_from(">Q", data, 0)[0]
        if protocol_id != MAGIC_CONN_ID:
            self.send_error(transaction_id, addr, "Invalid protocol ID.")
            return

        connection_id = random.randint(0, 0xFFFFFFFFFFFFFFFF)
        response = struct.pack(">IIQ", ACTION_CONNECT, transaction_id, connection_id)
        sock = self.server_ipv6 if is_ipv6 else self.server_ipv4
        sock.sendto(response, addr)

    def handle_announce(self, data, addr, is_ipv6):
        if len(data) < 98: 
            self.send_error(0, addr, "Invalid packet size for announce request.")
            return
        
        unpacked = struct.unpack(">QII20s20sQQQIIIiH", data[:98])

        print(f"handle announce {addr[0]}:{addr[1]}: {unpacked}")

        connection_id, action, transaction_id, info_hash, peer_id, downloaded, left, uploaded, event, ip, key, num_want, port = unpacked
        
        if action != ACTION_ANNOUNCE:
            self.send_error(transaction_id, addr, "Invalid action in announce request.")
            return
        
        info_hash = info_hash.hex()

        is_completed = 1 if left == 0 or event == EVENT_COMPLETED else 0

        status_map = {
            0: "",
            1: "completed",
            2: "started",
            3: "stopped"
        }
        event = status_map.get(event)

        peers = db.get_peers(info_hash=info_hash)
        this_peer_exists = db.is_duplicate(peer_id, info_hash)

        if this_peer_exists < 1:
            db.insert_peer(peer_id, 0, info_hash, addr[0], None, port, uploaded, downloaded, left, event, is_completed)
        else:
            db.update_peer(peer_id, 0, info_hash, is_completed, event, uploaded, downloaded, left)

        peers = db.get_peers_for_response(info_hash, min(num_want, MAX_NUM_WANT), peer_id)

        compact_peers = b"".join([
            socket.inet_pton(socket.AF_INET6 if ':' in peer["ip"] else socket.AF_INET, peer["ip"]) + struct.pack(">H", peer["port"]) 
            for peer in peers.values()
        ])
        print(f"announce response: {transaction_id} {INTERVAL} {len(peers)} {compact_peers}")
        response = struct.pack(">IIIII", ACTION_ANNOUNCE, transaction_id, INTERVAL, len(peers), 0) + compact_peers
        sock = self.server_ipv6 if is_ipv6 else self.server_ipv4
        sock.sendto(response, addr)

    def handle_scrape(self, data, addr, is_ipv6):
        if len(data) < 16:  # Check if the packet is at least 16 bytes for scrape
            self.send_error(0, addr, "Invalid packet size for scrape request.")
            return


        print(f"handle announce {addr[0]}:{addr[1]}: {unpacked}")
        unpacked = struct.unpack(">QII", data[:16])
        connection_id, action, transaction_id = unpacked

        if action != ACTION_SCRAPE:
            self.send_error(transaction_id, addr, "Invalid action in scrape request.")
            return


        info_hashes = [data[i:i+20].hex() for i in range(16, len(data), 20)]

        response_data = [struct.pack(">III", db.get_seeder_count(h), db.get_completed_count(h), db.get_leecher_count(h)) for h in info_hashes]

        response = struct.pack(">II", ACTION_SCRAPE, transaction_id) + b"".join(response_data)
        sock = self.server_ipv6 if is_ipv6 else self.server_ipv4
        sock.sendto(response, addr)