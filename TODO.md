# To-Do List

## Short Term

- **Add failure reason to scrape**  
  - Any `infohash` that fails to scrape will get a failure reason.
    Should we only return a failure reason if one fails? like announce?

- **Add fullscrape capability**  
  - If no `info_hashes` are given, scrape the whole peers list.  
  - **Add config option** to turn on/off this capability.

- **Add `no_peer_id` to data structures**  
  - Prevent accidental exposure of `peer_ids` when the client requests not to.

- **Implement peer selection algorithm**  
  - Return peers based on the client's request:
    - If the client is a **seeder** → Return peers with **incomplete clients**.
    - If the client is a **leecher** → Return peers with a **seeder**.
    - If the client is **close to completing** → Prioritize **superseeders** to maximize piece availability.
    - Use sorting/ordering to balance **superseeders, normal seeders, early-stage incompletes, and late-stage incompletes**.

- **Add `/stats` route**
  - **Add config options** to enable/disable each mode:
    - `?mode=everything`
    - `?mode=version`
    - `?mode=conn`
    - `?mode=torr`

### `/stats` Route Data

- **Version (`?mode=version`)**
  - Program name  
  - Program version  
  - Release date  
  - Author  
  - Registration info  

- **Connection Stats (`?mode=conn`)**
  - Total successful announces  
  - Total successful scrapes  
  - Total failed announces  
  - Total failed scrapes  
  - Total connections  
  - Full scrape count (all peers)  
  - Full scrape size (bytes, all peers, in whatever storage mode we're using)  
  - Overall bandwidth in  
  - Overall bandwidth out  

- **Torrent Stats (`?mode=torr`)**
  - Total torrent count  
  - Total seed count  
  - Total peer count  
  - Total leech count  
  - Total completed count  

## Mid Term

- **Rate-limiting**
  - Limit individual methods. Offenders get blacklisted.

- **Blacklist**
  - Block or deny requests from IPs.  
  - Directly modify `iptables` using `from pyroute2 import IPRoute`.

- **Add TCP and UDP servers**
  - Support concurrent operation of all servers, a combination, or just one.
