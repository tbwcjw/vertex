# To-Do List

## Short Term
- Fix insert peer logic. should insert new peers, right now it is looking for
  infohash, and updating if it finds the infohash. only one peer per torrent
  is inserted right now.

- Make peer_id's hexidecimal

- Interval/Min Interval based on system load/connections? 

- Model UDP request/responses

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

- **Logging**
  - Logging levels: error, warning, caution, info

- **Rate-limiting**
  - Limit individual methods. Offenders get blacklisted.

- **Blacklist**
  - Block or deny requests from IPs.  
  - Directly modify `iptables` using `from pyroute2 import IPRoute`.
