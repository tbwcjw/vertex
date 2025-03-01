import random
import requests

#http test

STATUSES = ["started", "completed", "stopped"]
COMPACT = 1
METHOD = "http://"
HOST = "127.0.0.1"
PORT = 5000
INFO_HASHES = ["01234567890123456789", "98765432109876543210", "qwertyuiopasdfghjklz"]
SLEEP = 2
count = 0
while True:
    filesize = random.randint(100,1000000000)
    downloaded = random.randint(100, filesize)
    left = filesize - downloaded
    uploaded = random.randint(round(downloaded/10), round(downloaded/5))
    count = count+1
    peer_id = f"testpeer_{count:0{20-len('testpeer_')}}"
    info_hash = random.choice(INFO_HASHES)
    ip = f"{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
    port = random.randint(2049, 65525)
    num_want = random.randint(0,255)
    event = random.choice(STATUSES)
    url = f"{METHOD}{HOST}:{PORT}/announce?info_hash={info_hash}&ip={ip}&port={port}&compact={COMPACT}&num_want={num_want}&peer_id={peer_id}&event={event}&downloaded={downloaded}&left={left}&uploaded={uploaded}"
    response = requests.get(url)
    
    print(f"REQUEST {url}\nSTATUS CODE: {response.status_code}\nBODY:\n{response.text}")