#!/usr/bin/env python3
"""
Database module for Sentinel monitoring system.
Handles all SQLite operations for storing and retrieving miner and system stats.
"""

import sqlite3
import datetime
from contextlib import contextmanager
from typing import Optional, List, Dict, Any
import config


class SentinelDB:
    """Manages the SQLite database for Sentinel monitoring."""
    
    def __init__(self, db_path: str = config.DB_PATH):
        self.db_path = db_path
        self.initialize_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def initialize_database(self):
        """Creates the database schema if it doesn't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Enable WAL mode for better concurrent access
            # This is especially important when sharing DB over network (NFS/SMB)
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA busy_timeout=5000")  # Wait up to 5 seconds if locked
            cursor.execute("PRAGMA synchronous=NORMAL")  # Balance safety and speed
            
            # Miners table - stores miner status and stats
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS miners (
                    host TEXT PRIMARY KEY,
                    last_seen TIMESTAMP NOT NULL,
                    hashrate REAL,
                    cpu_usage REAL,
                    ram_usage REAL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Miner history table - stores time-series data
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS miner_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    host TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    hashrate REAL,
                    cpu_usage REAL,
                    ram_usage REAL,
                    status TEXT NOT NULL,
                    FOREIGN KEY (host) REFERENCES miners(host)
                )
            """)
            
            # P2Pool stats table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS p2pool_stats (
                    miner_address TEXT PRIMARY KEY,
                    last_seen TIMESTAMP NOT NULL,
                    blocks_found TEXT,
                    shares_held INTEGER,
                    payouts_sent TEXT,
                    active_shares INTEGER,
                    active_uncles INTEGER,
                    total_shares INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # P2Pool history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS p2pool_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    miner_address TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    active_shares INTEGER,
                    total_shares INTEGER,
                    FOREIGN KEY (miner_address) REFERENCES p2pool_stats(miner_address)
                )
            """)
            
            # Security alerts table (for NIDS)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP NOT NULL,
                    type TEXT NOT NULL,
                    details TEXT NOT NULL,
                    acknowledged INTEGER DEFAULT 0,
                    severity TEXT DEFAULT 'medium',
                    source_ip TEXT,
                    source_mac TEXT
                )
            """)
            
            # Create indexes for better query performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_miner_history_host_time 
                ON miner_history(host, timestamp DESC)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_p2pool_history_address_time 
                ON p2pool_history(miner_address, timestamp DESC)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_alerts_timestamp 
                ON alerts(timestamp DESC)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_alerts_acknowledged 
                ON alerts(acknowledged, timestamp DESC)
            """)
    
    def upsert_miner(self, host: str, hashrate: Optional[float], 
                     cpu: Optional[float] = None, ram: Optional[float] = None):
        """
        Insert or update miner stats.
        Also adds an entry to the history table.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            timestamp = datetime.datetime.now(datetime.timezone.utc)
            status = "Online" if hashrate is not None else "Offline"
            
            # Update or insert into miners table
            cursor.execute("""
                INSERT INTO miners (host, last_seen, hashrate, cpu_usage, ram_usage, status)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(host) DO UPDATE SET
                    last_seen = excluded.last_seen,
                    hashrate = excluded.hashrate,
                    cpu_usage = excluded.cpu_usage,
                    ram_usage = excluded.ram_usage,
                    status = excluded.status
            """, (host, timestamp, hashrate, cpu, ram, status))
            
            # Add to history
            cursor.execute("""
                INSERT INTO miner_history (host, timestamp, hashrate, cpu_usage, ram_usage, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (host, timestamp, hashrate, cpu, ram, status))
    
    def upsert_p2pool_stats(self, miner_address: str, blocks_found: str, 
                           shares_held: int, payouts_sent: str,
                           active_shares: int, active_uncles: int, 
                           total_shares: int):
        """Insert or update P2Pool stats."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            timestamp = datetime.datetime.now(datetime.timezone.utc)
            
            # Update or insert into p2pool_stats table
            cursor.execute("""
                INSERT INTO p2pool_stats 
                (miner_address, last_seen, blocks_found, shares_held, payouts_sent,
                 active_shares, active_uncles, total_shares)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(miner_address) DO UPDATE SET
                    last_seen = excluded.last_seen,
                    blocks_found = excluded.blocks_found,
                    shares_held = excluded.shares_held,
                    payouts_sent = excluded.payouts_sent,
                    active_shares = excluded.active_shares,
                    active_uncles = excluded.active_uncles,
                    total_shares = excluded.total_shares
            """, (miner_address, timestamp, blocks_found, shares_held, payouts_sent,
                  active_shares, active_uncles, total_shares))
            
            # Add to history
            cursor.execute("""
                INSERT INTO p2pool_history (miner_address, timestamp, active_shares, total_shares)
                VALUES (?, ?, ?, ?)
            """, (miner_address, timestamp, active_shares, total_shares))
    
    def get_all_miners(self, online_only: bool = False) -> List[Dict[str, Any]]:
        """Retrieve all miners from the database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM miners"
            if online_only:
                query += " WHERE status = 'Online'"
            query += " ORDER BY last_seen DESC"
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
    
    def get_miner(self, host: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific miner's current stats."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM miners WHERE host = ?", (host,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_miner_history(self, host: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Retrieve historical data for a specific miner."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=hours)
            
            cursor.execute("""
                SELECT * FROM miner_history 
                WHERE host = ? AND timestamp > ?
                ORDER BY timestamp ASC
            """, (host, cutoff))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_all_p2pool_stats(self) -> List[Dict[str, Any]]:
        """Retrieve all P2Pool stats."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM p2pool_stats ORDER BY last_seen DESC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_p2pool_history(self, miner_address: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Retrieve historical P2Pool data for a specific miner."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=hours)
            
            cursor.execute("""
                SELECT * FROM p2pool_history 
                WHERE miner_address = ? AND timestamp > ?
                ORDER BY timestamp ASC
            """, (miner_address, cutoff))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def cleanup_old_data(self, days: int = config.DATA_RETENTION_DAYS):
        """Remove data older than specified days."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
            
            cursor.execute("DELETE FROM miner_history WHERE timestamp < ?", (cutoff,))
            cursor.execute("DELETE FROM p2pool_history WHERE timestamp < ?", (cutoff,))
            
            deleted_miner = cursor.rowcount
            
            print(f"Cleaned up {deleted_miner} old records from history tables.")
    
    def get_database_stats(self) -> Dict[str, int]:
        """Get statistics about the database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            cursor.execute("SELECT COUNT(*) FROM miners")
            stats['total_miners'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM miners WHERE status = 'Online'")
            stats['online_miners'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM miner_history")
            stats['history_records'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM p2pool_stats")
            stats['p2pool_miners'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM alerts WHERE acknowledged = 0")
            stats['unacknowledged_alerts'] = cursor.fetchone()[0]
            
            return stats
    
    def add_alert(self, alert_type: str, details: str, severity: str = "medium",
                  source_ip: str = None, source_mac: str = None):
        """Add a security alert to the database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            timestamp = datetime.datetime.now(datetime.timezone.utc)
            
            cursor.execute("""
                INSERT INTO alerts (timestamp, type, details, severity, source_ip, source_mac)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (timestamp, alert_type, details, severity, source_ip, source_mac))
    
    def get_alerts(self, acknowledged: bool = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve security alerts from the database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM alerts"
            params = []
            
            if acknowledged is not None:
                query += " WHERE acknowledged = ?"
                params.append(1 if acknowledged else 0)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def acknowledge_alert(self, alert_id: int):
        """Mark an alert as acknowledged."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE alerts SET acknowledged = 1 WHERE id = ?", (alert_id,))
    
    def acknowledge_all_alerts(self):
        """Mark all alerts as acknowledged."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE alerts SET acknowledged = 1")
    
    def delete_alert(self, alert_id: int):
        """Delete a specific alert."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM alerts WHERE id = ?", (alert_id,))
