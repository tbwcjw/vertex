import builtins
import sys
from tracker_http import app
from threading import Thread
import time

import schedule
from configloader import ConfigLoader
from storagemanager import StorageManager
from tracker_udp import UDPTracker
from waitress import serve

from log import Log, LogLevel

config = ConfigLoader()
db = StorageManager(config.get('storage.type'))

def run_schedule():
    if config.get('storage.cleanup_job'):
        schedule.every().day.at(config.get('storage.cleanup_at')).do(db.cleanup_peers)
    
    jobs = schedule.get_jobs()
    if jobs:
        for job in jobs:
            print(f"Scheduled Job: {job.job_func.__name__}, Interval: {job.interval} {job.unit}, Next Run: {job.next_run}")
    else:
        print(f"Scheduler didn't find any jobs")

    while True:
        schedule.run_pending()
        time.sleep(1)    

def run_http():
    print(f"HTTP Tracker started on: {config.get('http.ip_bind')}:{config.get('http.ip_port')}")
    serve(app, host=config.get('http.ip_bind'), port=config.get('http.ip_port'), threads=config.get('http.threads'))
    
def run_udp():
    udp_tracker = UDPTracker(
                ipv4_ip=config.get('udp.ipv4_bind'),
                ipv4_port=config.get('udp.ipv4_port'),
                ipv6_ip=config.get('udp.ipv6_bind'),
                ipv6_port=config.get('udp.ipv6_port'))
    udp_tracker.run()

if __name__ == "__main__":
    scheduler_thread = Thread(target=run_schedule, name="scheduler")
    scheduler_thread.start()
    if config.get('http.server_enable'):
        http_process = Thread(target=run_http, name="tracker_http")
        http_process.start()
    if config.get('udp.server_enable'):
        if config.get('tracker.private'):
            print(f"UDP tracker cannot be private. not starting udp tracker", log_level=LogLevel.WARNING)
        else:
            udp_process = Thread(target=run_udp, name="tracker_udp")
            udp_process.start()
