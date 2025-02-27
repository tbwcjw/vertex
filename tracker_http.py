import socket
import struct
import time

import urllib

from pydantic import ValidationError
from bencoding import Bencoding
from flask import Flask, request, Response, g
import ipaddress

from bencoding import Bencoding
from storagemanager import StorageManager
from configloader import ConfigLoader

from models import Announce, AnnounceResponse, ScrapeResponse, ScrapeResult

from stats import stats_bp, conn_stats

from log import Log, LogLevel

config = ConfigLoader()
db = StorageManager(config.get('storage.type'))
bc = Bencoding

app = Flask(__name__)
app.register_blueprint(stats_bp)

PRIVATE = config.get('tracker.private')
PASSKEY = config.get('tracker.passkey')
MAX_NUM_WANT = config.get('tracker.max_num_want')
INTERVAL = config.get('tracker.interval')
MIN_INTERVAL = config.get('tracker.min_interval')
MIN_SCRAPE_INTERAL = config.get('tracker.min_scrape_interval')
TRACKER_ID = config.get('tracker.tracker_id')

@app.before_request
def rx_stats():
    conn_stats.update(key="http requests", value=1)
    conn_stats.update(key="rx size", value=len(request.url))
    return

@app.after_request
def tx_stats(response):
    conn_stats.update(key="http responses", value=1)
    conn_stats.update(key="tx size", value=len(response.data))
    return response

@app.errorhandler(ValidationError)
def handle_validation_error(error):
    errors = [{"loc": err['loc'], "msg": err['msg']} for err in error.errors()]
    result = ", ".join(f"{err['loc']}: {err['msg']}" for err in errors)

    conn_stats.update(key="announce fail", value=1)
    print(result, log_level="ERROR")
    return Response(bc.encode({"failure reason": result}), mimetype='text/plain')

@app.route("/scrape", methods=["GET"])
def scrape():
    info_hashes = request.args.getlist('info_hash')
    results = {}

    # fullscrape
    if not info_hashes:  
        if config.get('tracker.fullscrape'):  
            info_hashes = db.fullscrape()  
        else:  
            conn_stats.update(key="scrape fail", value=1)
            return Response(bc.encode({"failure reason": "fullscrape not enabled"}), mimetype='text/plain')

    for info_hash in info_hashes:
        result = db.get_peers(info_hash)
        print(result)
        if len(result) < 1:
            conn_stats.update(key="scrape fail", value=1)
            return Response(bc.encode({"failure reason": f"info_hash {info_hash} not found"}), mimetype='text/plain')

        complete = 0
        downloaded = 0
        incomplete = 0

        for res in result:
            complete += res['is_completed']
            if res['last_event'] == "completed" or (res['is_completed'] and res['left'] < 1):
                downloaded += 1
            if not res['is_completed'] or res["left"] > 0:
                incomplete += 1

        results[info_hash] = ScrapeResult(
            complete=complete,
            downloaded=downloaded,
            incomplete=incomplete
        )

    if not results: 
        conn_stats.update(key="scrape fail", value=1)
        return Response(bc.encode({"failure reason": "no valid info_hashes found"}), mimetype='text/plain')

    response_data = ScrapeResponse(
        flags={'min_request_interval': MIN_SCRAPE_INTERAL},
        files=results
    )

    conn_stats.update(key="scrape success", value=1)
    return Response(bc.encode(response_data.dict()), mimetype='text/plain')



#decode infohash from client
def decode_info_hash(string):
    return urllib.parse.unquote_to_bytes(string).hex()

#network byte order ip+port for compact string
def pack_ip_port(ip, port):
    result = b""
    ip_bytes = socket.inet_aton(ip)   #4 byte binary
    port_bytes = struct.pack("!H", port) #2 byte big edian
    result = ip_bytes + port_bytes
    return result

@app.route("/announce", methods=["GET"])
def announce():
    start_time = time.time()
    #check if client remote addr is ipv4 or ipv6
    client_ip = request.args.get('ip') or request.remote_addr
    if isinstance(client_ip, ipaddress.IPv6Address):
        client_ipv6 = client_ip
        ipv4port = None
        ipv6port = request.args.get('port')
        client_ip = None
        print(f"client is ipv6")
    else:
        ipv4port = request.args.get('port')
        ipv6port = None
        client_ipv6 = None
        print(f"client is ipv4")
    print(request.url)

    compact = request.args.get('compact') == '1'
    peer_id = request.args.get('peer_id')

    print(f"PEER ID {peer_id}",log_level=LogLevel.DEBUG)
    #clamp max_want
    num_want = min(int(request.args.get('numwant', 0)), MAX_NUM_WANT)

    info_hash = decode_info_hash(request.args.get('info_hash'))
    count = db.get_seeder_count(info_hash=info_hash)
    print(f"seeders for {info_hash}: {count}")

    data = Announce(
        ipv4 = client_ip,
        ipv6 = client_ipv6,
        info_hash = info_hash,
        peer_id = peer_id,
        no_peer_id = request.args.get('no_peer_id', 0),
        key = request.args.get('key'),
        port = ipv4port,
        ipv6port = ipv6port,
        downloaded = request.args.get('downloaded', 0),
        uploaded = request.args.get('uploaded', 0),
        left = request.args.get('left', 0),
        passkey = request.args.get('passkey'),          #todo, find spec for 
        event = request.args.get('event'),
        numwant = num_want,
        compact = request.args.get('compact')
    )

    is_completed = 1 if data.left == 0 or data.event == "completed" else 0

    print(data.model_dump())
    
    if PRIVATE and data.passkey != PASSKEY:
        conn_stats.update(key="announce fail", value=1)
        return Response(bc.encode({"failure reason": "error private tracker, check passkey"}), mimetype='text/plain')
    

    peers = db.get_peers(info_hash=data.info_hash)

    this_peer_exists = db.is_duplicate(peer_id, info_hash)

    if this_peer_exists < 1:
        db.insert_peer(data.peer_id, data.no_peer_id, data.info_hash, data.ipv4, data.ipv6, data.port, data.uploaded, data.downloaded, data.left, data.event, is_completed)
    else:
        db.update_peer(data.peer_id, data.no_peer_id, data.info_hash, is_completed, data.event, data.uploaded, data.downloaded, data.left)


    if data.compact:
        compact = b""
        peers = db.get_peers_for_response(info_hash, data.numwant, data.peer_id)
        for peer in peers.values():
            ip = peer["ip"]
            port = peer["port"]

            compact += pack_ip_port(ip, port)
            
        peers = bc.encode(compact)

        response = AnnounceResponse(
            interval = INTERVAL,
            min_interval = MIN_INTERVAL,
            completed = db.get_seeder_count(info_hash=data.info_hash),
            incomplete = db.get_leecher_count(info_hash=data.info_hash),
            peers = peers, # binary model for compact
            tracker_id = TRACKER_ID
        )
    else:
        response = AnnounceResponse(
            interval = INTERVAL,
            min_interval = MIN_INTERVAL,
            completed = db.get_seeder_count(info_hash=data.info_hash),
            incomplete = db.get_leecher_count(info_hash=data.info_hash),
            peers = db.get_peers_for_response(info_hash, data.numwant, data.peer_id), # dictionary model
            tracker_id= TRACKER_ID
        )
        print(response.peers)

    end_time = time.time()
    elapsed = end_time - start_time
    print(f"elapsed time: {elapsed}", log_level=LogLevel.DEBUG)
    conn_stats.update(key="announce success", value=1)
    return Response(bc.encode(response.dict()), mimetype='text/plain')
