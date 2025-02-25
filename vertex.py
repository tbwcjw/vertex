from multiprocessing import Process
from tracker_http import app
from threading import Thread
import time

import schedule
from configloader import ConfigLoader
from storagemanager import StorageManager
from tracker_udp import UDPTracker

config = ConfigLoader()
db = StorageManager(config.get('storage.type'))

def run_schedule():
    schedule.every().day.at(config.get('storage.cleanup_at')).do(db.cleanup_peers)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

def run_udp():
    udp_tracker = UDPTracker(
        ipv4_ip=config.get('udp.ipv4_bind'),
        ipv4_port=config.get('udp.ipv4_port'),
        ipv6_ip=config.get('udp.ipv6_bind'),
        ipv6_port=config.get('udp.ipv6_port'))
    udp_tracker.run()

def run_http():
    app.run(host=config.get('http.ip_bind'), port=config.get('http.ip_port'), threaded=True)
     
if __name__ == "__main__":
    if config.get('storage.run_schedule'):
        scheduler_thread = Thread(target=run_schedule, name="scheduler")
        scheduler_thread.start()
    if config.get('http.server_enable'):
        http_process = Thread(target=run_http, name="tracker_http")
        http_process.start()
    if config.get('udp.server_enable'):
        if config.get('tracker.private'):
            print(f"UDP tracker cannot be private. not starting udp tracker")
        else:
            udp_thread = Thread(target=run_udp, name="tracker_udp_parent")
            udp_thread.start()
        