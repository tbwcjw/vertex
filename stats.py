from flask import Blueprint, Response, jsonify
from configloader import ConfigLoader
import pkg_resources

from storagemanager import StorageManager

# Create a Blueprint for stats
stats_bp = Blueprint('stats', __name__)

# Metadata
__title__ = "vertex"
__author__ = "tbwcjw"
__email__ = "me@tbwcjw.online"
__license__ = "MIT"


class ConnStats:
    def __init__(self):
        self.conn_stats = {
            "announce success": 0,
            "announce fail": 0,
            "scrape success": 0,
            "scrape fail": 0,
            "http requests": 0,
            "http responses": 0,
            "udp connect success": 0,
            "udp connect fail": 0,
            "tx size": 0,
            "rx size": 0
        }

    def update(self, key, value):
        self.conn_stats[key] = self.conn_stats[key] + value

    def get(self, key=None):
        if key is None:
            return self.conn_stats
        return self.conn_stats[key]

conn_stats = ConnStats()
config = ConfigLoader()
db = StorageManager(config.get('storage.type'))

from flask import request, Response

@stats_bp.route('/stats', methods=["GET"])
def handle_stats():
    if not config.get('stats.stats_enabled'):
        return Response("stats not enabled", mimetype='text/plain')

    mode = request.args.get('mode')
    if not mode:
        return Response("mode parameter is required", mimetype='text/plain')

    handlers = {
        'everything': handle_everything,
        'version': handle_version,
        'conn': handle_conn,
        'config': handle_config,
        'torr': handle_torr,
    }

    handler = handlers.get(mode)
    if handler:
        return handler()
    else:
        return Response("invalid mode", mimetype='text/plain')

def handle_config():
    if not config.get('stats.config_enabled'):
        return Response("mode disabled", mimetype='text/plain')
    return Response(config.all_items_as_string(), mimetype='text/plain')

def handle_torr():
    if not config.get('stats.torr_enabled'):
        return Response("mode disabled", mimetype='text/plain')
    total_unique_info_hashes = db.get_unique_infohash_count()
    all_peer_count = db.get_all_peer_count()
    all_seeder_count = db.get_all_seeder_count()
    all_leecher_count = db.get_all_leecher_count()
    all_events = db.get_all_event_counts()
    started = all_events.get("started", 0)
    stopped = all_events.get("stopped", 0)
    completed = all_events.get("completed", 0)
    return Response(f"unique infohashes: {total_unique_info_hashes}\nall peers: {all_peer_count}\nall seeders: {all_seeder_count}\nall leechers: {all_leecher_count}\nstarted: {started}\nstopped: {stopped}\ncompleted: {completed}", mimetype='text/plain')

def handle_conn():
    if not config.get('stats.conn_enabled'):
        return Response("mode disabled", mimetype='text/plain')
    total_requests = conn_stats.get()
    return Response("\n".join(f"{k}: {v}" for k, v in total_requests.items()), mimetype='text/plain')

def handle_version():
    if not config.get('stats.version_enabled'):
        return Response("mode disabled", mimetype='text/plain')
    
    version_string = f"{__title__} - {__author__} <{__email__}> - {__license__} license\n\npackages:\n" + '\n'.join(f"{package.project_name}: {package.version}" for package in pkg_resources.working_set)
    return Response(version_string, mimetype='text/plain')

def handle_everything():
    if not config.get('stats.everything_enabled'):
        return Response("mode disabled", mimetype='text/plain')
    conn_status = handle_conn().get_data(as_text=True)
    version_info = handle_version().get_data(as_text=True)
    config_info = handle_config().get_data(as_text=True)
    torr_info = handle_torr().get_data(as_text=True)
    combined_response = f"torr:\n{torr_info}\n\nconnection:\n{conn_status}\n\nconfig:\n{config_info}\n\nversion:\n{version_info}"
    return Response(combined_response, mimetype='text/plain')

