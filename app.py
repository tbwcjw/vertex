import socket
import struct
import sys
from threading import Thread
import time
from typing import Any, Dict, Literal, Optional, Union

import urllib
from bencoding import Bencoding
from flask import Flask, json, jsonify, request, Response
from pydantic import BaseModel, ValidationError, constr, conint, validator
import ipaddress

from bencoding import Bencoding
from storagemanager import StorageManager
from configloader import ConfigLoader

import schedule

config = ConfigLoader()
db = StorageManager(config.get('storage.type'))
bc = Bencoding
app = Flask(__name__)

PRIVATE = config.get('tracker.private')
PASSKEY = config.get('tracker.passkey')
MAX_NUM_WANT = config.get('tracker.max_num_want')
INTERVAL = config.get('tracker.interval')
MIN_INTERVAL = config.get('tracker.min_interval')
TRACKER_ID = config.get('tracker.tracker_id')

class Announce(BaseModel):
    ipv4: Optional[str] = None
    ipv6: Optional[str] = None
    info_hash: constr(min_length=20, max_length=2000, strict=True) = None
    peer_id:  Optional[constr(min_length=20, max_length=20, strict=True)]
    key: Optional[str] = None
    port: conint(ge=0, le=65535)
    ipv6port: None
    downloaded: conint(ge=0, le=sys.maxsize)
    uploaded: conint(ge=0, le=sys.maxsize)
    left: conint(ge=0, le=sys.maxsize)
    passkey: Optional[str] = None
    event: Optional[Literal["started", "stopped", "completed"]] = ""
    numwant: Optional[conint(ge=0, le=sys.maxsize)] = 150
    compact: Optional[conint(ge=0, le=1)] = 0

class AnnounceResponse(BaseModel):
    failure_reason: Optional[str] = None
    warning_message: Optional[str] = None
    interval: Optional[conint(ge=0, le=sys.maxsize)] = INTERVAL
    min_interval: Optional[conint(ge=0, le=sys.maxsize)] = MIN_INTERVAL
    complete: Optional[conint(ge=0, le=sys.maxsize)] = None
    incomplete: Optional[conint(ge=0, le=sys.maxsize)] = None
    peers: Optional[Union[dict, bytes]] = None
    tracker_id: Optional[constr(min_length=6, max_length=20, strict=True)] = TRACKER_ID

    #it makes sense that the request has underscores...
    #so why not the response too?
    def dict(self, *args, **kwargs):
        original_dict = super().dict(*args, **kwargs)
        return {k.replace('_', ' '): v for k, v in original_dict.items() if v}

    #as per spec, if failure reason is given no other responses will be given
    @validator('failure_reason', pre=True, always=True)
    def check_failure_reason(cls, v, values):
        if v is not None:
            values['warning_message'] = None
            values['interval'] = None
            values['min_interval'] = None
            values['complete'] = None
            values['incomplete'] = None
            values['peers'] = None
        return v

@app.errorhandler(ValidationError)
def handle_validation_error(error):
    errors = [{"loc": err['loc'], "msg": err['msg']} for err in error.errors()]
    result = ", ".join(f"{err['loc']}: {err['msg']}" for err in errors)

    return Response(bc.encode({"failure reason": result}), mimetype='text/plain')

class ScrapeResult(BaseModel):
    complete: conint(ge=0) 
    downloaded: conint(ge=0)
    incomplete: conint(ge=0)

class ScrapeResponse(BaseModel):
    flags: Dict[str, Any]
    results: Dict[str, ScrapeResult]


@app.route("/scrape", methods=["GET"])
def scrape():
    info_hashes = request.args.getlist('info_hash')
    type = request.args.get('type')
    results = {} 

    for info_hash in info_hashes:
        result = db.get_peers(info_hash)

        complete = 0
        downloaded = 0
        incomplete = 0

        for res in result:
            complete += res['is_completed']
            if res['last_event'] == "completed" or res['is_completed'] and res['left'] < 1:
                downloaded += 1
            if not res['is_completed'] or res["left"] > 0:
                incomplete += 1

        results[info_hash] = ScrapeResult(
            complete=complete,
            downloaded=downloaded,
            incomplete=incomplete
        )
        response_data = ScrapeResponse(
        flags={'min_request_interval': MIN_INTERVAL},
        results=results
    )


    if type == 'json':
        return jsonify(results), 200
    return Response(bc.encode(response_data.dict()), mimetype='text/plain')


#decode infohash from client
def decode_info_hash(string):
    return urllib.parse.unquote_to_bytes(string).hex()


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
    #honor no peer id
    #spec says to ignore no_peer_id when using compact
    no_peer_id = request.args.get('no_peer_id') == '1'
    compact = request.args.get('compact') == '1'
    peer_id = request.args.get('peer_id')

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
        return Response(bc.encode({"failure reason": "error private tracker, check passkey"}), mimetype='text/plain')
    
    peers = db.get_peers(info_hash=data.info_hash)


    if len(peers) < 1:
        db.insert_peer(data.peer_id, data.info_hash, data.ipv4, data.ipv6, data.port, data.uploaded, data.downloaded, data.left, data.event, is_completed)
    else:
        print('UPDATING PEER')
        db.update_peer(data.peer_id, data.info_hash, is_completed, data.event, data.uploaded, data.downloaded, data.left)

    if data.compact:
        compact = b""
        peers = db.get_peers_for_response(info_hash, data.numwant)
        for peer in peers.values():
            ip = peer["ip"]
            port = peer["port"]

            ip_bytes = socket.inet_aton(ip)   #4 byte binary
            port_bytes = struct.pack("!H", port)  #2 byte big edian
            compact += ip_bytes + port_bytes
            
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
            peers = db.get_peers_for_response(info_hash, data.numwant), # dictionary model
            tracker_id= TRACKER_ID
        )

    end_time = time.time()
    elapsed = end_time - start_time
    print(f"elapsed time: {elapsed}")
    return Response(bc.encode(response.dict()), mimetype='text/plain')

def run_schedule():
    #todo \/ make this work with config file
    schedule.every().day.at(config.get('storage.cleanup_at')).do(db.cleanup_peers)
    
    while True:
        schedule.run_pending()
        time.sleep(1)
        
if __name__ == "__main__":
    scheduler_thread = Thread(target=run_schedule)
    scheduler_thread.start()
    app.run("127.0.0.1", 5000, debug=True)

    
    
