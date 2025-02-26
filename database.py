import sqlite3

from storageinterface import StorageInterface
from configloader import ConfigLoader
from log import Log

config = ConfigLoader()

OLDER_THAN = f"-{config.get('remove_older_than')}"


class Database(StorageInterface):
    def __init__(self, db_name=config.get('storage.db_name')):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.cursor.execute('PRAGMA journal_mode=WAL;') 
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS peers (
                peer_id TEXT NULL,
                no_peer_id BOOLEAN DEFAULT false NOT NULL,
                info_hash TEXT,
                ipv4 TEXT NULL,
                ipv6 TEXT NULL,
                port INTEGER NOT NULL,
                is_completed BOOLEAN DEFAULT false NOT NULL,
                last_event TEXT NULL,
                uploaded INTEGER DEFAULT 0,
                downloaded INTEGER DEFAULT 0,
                left INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def get_unique_infohash_count(self):
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(DISTINCT info_hash) AS unique_count FROM peers")
            count = cursor.fetchone()[0]
        return count
    
    def get_all_peer_count(self):
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM peers")
            count = cursor.fetchone()[0]
        return count
    
    def get_all_seeder_count(self):
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM peers WHERE is_completed = 1 AND last_event != 'stopped'")
            count = cursor.fetchone()[0]
        return count
    
    def get_all_event_counts(self):
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute("SELECT last_event, COUNT(*) FROM peers WHERE last_event in ('started', 'stopped', 'completed') GROUP BY last_event")
            result = dict(cursor.fetchall())
        return result
    
    def get_all_leecher_count(self):
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM peers WHERE is_completed = 0 AND last_event != 'stopped'")
            count = cursor.fetchone()[0]
        return count
    
    def get_seeder_count(self, info_hash):
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM peers WHERE info_hash = ? AND is_completed = 1", (info_hash,))
            count = cursor.fetchone()[0]
        return count
        
    def get_leecher_count(self, info_hash):
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM peers WHERE info_hash = ? AND is_completed = 0", (info_hash,))
            count = cursor.fetchone()[0]
        return count
    
    def get_peers(self, info_hash):
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM peers WHERE info_hash = ?", (info_hash,))
            result = cursor.fetchall()
        return result
    
    def fullscrape(self):
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute("SELECT info_hash FROM peers")
            result = [row[0] for row in cursor.fetchall()]
        return result
    
    def get_peers_for_response(self, info_hash, numwant, peer_id):
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute('''SELECT peer_id, no_peer_id, COALESCE(ipv4, ipv6) AS ip, port FROM peers WHERE info_hash = ? AND peer_id != ? LIMIT ?''', (info_hash, peer_id, numwant,))
            
            result = cursor.fetchall()
            
            return {
                (row['peer_id'] if not row['no_peer_id'] else f"anon_{index}"): 
                {"ip": row['ip'], "port": row['port']} 
                for index, row in enumerate(result)
            }
    
    def insert_peer(self, peer_id, no_peer_id, info_hash, ipv4, ipv6, port, uploaded, downloaded, left, last_event, is_complete):
        with self.conn:
            self.conn.execute("INSERT INTO peers (peer_id, no_peer_id, info_hash, ipv4, ipv6, port, uploaded, downloaded, left, last_event, is_completed) VALUES (?,?,?,?,?,?,?,?,?,?,?)", (peer_id, no_peer_id, info_hash, ipv4, ipv6, port, uploaded, downloaded, left, last_event, is_complete))

    def is_duplicate(self, peer_id, info_hash):
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM peers WHERE peer_id = ? AND info_hash = ?", (peer_id, info_hash,))
            result = cursor.fetchone()[0]
            return result
        
    def update_peer(self, peer_id, no_peer_id, info_hash, is_complete, last_event, uploaded, downloaded, left):
        try:
            with self.conn:
                if last_event == "" or last_event is None:
                    self.conn.execute("UPDATE peers SET no_peer_id = ?, is_completed = ?, last_updated = CURRENT_TIMESTAMP, uploaded = ?, downloaded = ?, left = ? WHERE info_hash = ? AND peer_id = ?", (no_peer_id, is_complete, uploaded, downloaded, left, info_hash, peer_id,))
                else:
                    self.conn.execute("UPDATE peers SET no_peer_id = ?, is_completed = ?, last_event = ?, last_updated = CURRENT_TIMESTAMP, uploaded = ?, downloaded = ?, left = ? WHERE info_hash = ? AND peer_id = ?", (no_peer_id, is_complete, last_event, uploaded, downloaded, left, info_hash, peer_id,))
        except Exception as e:
            print(e)

    def cleanup_peers(self):
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute(f"DELETE FROM peers WHERE last_updated < datetime('now', '{OLDER_THAN}')")
            print(f"Cleaned up peers removed {cursor.rowcount} peer entries")