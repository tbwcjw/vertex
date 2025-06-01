# To-Do List

## Short Term
- Interval/Min Interval based on system load/connections? 
- Numwant return count based on system load/connections?

- Model UDP request/responses

- nonblocking flask/sqlite

- **Implement peer selection algorithm**  
  - Return peers based on the client's request:
    - If the client is a **seeder** → Return peers with **incomplete clients**.
    - If the client is a **leecher** → Return peers with a **seeder**.
    - If the client is **close to completing** → Prioritize **superseeders** to maximize piece availability.
    - Use sorting/ordering to balance **superseeders, normal seeders, early-stage incompletes, and late-stage incompletes**.

## Mid Term

- **Rate-limiting**
  - Limit individual methods. Offenders get blacklisted.

- **Blacklist**
  - Block or deny requests from IPs.  
  - Directly modify `iptables` using `from pyroute2 import IPRoute`.

  **Testing**
  - More comprehensive testing methodologies and implementations.
