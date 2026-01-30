#!/usr/bin/env python3
"""
Sentinel Probe: A tool for monitoring system status, Monero miners, and network security.
Refactored version using local SQLite database instead of Firestore.
"""

import psutil
import datetime
import requests
import argparse
import ipaddress
import sys
from typing import Optional, Tuple

# --- Configuration ---
import config
from database import SentinelDB

# --- Local Imports ---
# This will allow us to run the NIDS as part of the probe
try:
    from nids import start_nids_sniffer
    NIDS_AVAILABLE = True
except ImportError:
    NIDS_AVAILABLE = False
    def start_nids_sniffer(interface=None):
        print("Probe: NIDS module not found. Skipping.")


# Initialize database
db = SentinelDB()


def get_monero_hashrate(host: str = "127.0.0.1", port: int = config.DEFAULT_MINER_PORT) -> Optional[float]:
    """
    Queries the Monero miner API for hashrate.
    
    Args:
        host: Hostname or IP address of the miner
        port: API port
        
    Returns:
        Hashrate in H/s, or None if unavailable
    """
    api_url = f"http://{host}:{port}/2/summary"
    headers = {"Authorization": f"Bearer {config.MINER_API_TOKEN}"}
    
    try:
        response = requests.get(api_url, headers=headers, timeout=config.MINER_API_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        hashrate = data.get("hashrate", {}).get("total", [0])[0]
        return hashrate
    except requests.exceptions.Timeout:
        print(f"Warning: Timeout connecting to {host}:{port}")
        return None
    except requests.exceptions.ConnectionError:
        print(f"Warning: Could not connect to {host}:{port}")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"Warning: HTTP error from {host}:{port} - {e}")
        return None
    except (KeyError, IndexError, ValueError) as e:
        print(f"Warning: Unexpected response format from {host}:{port} - {e}")
        return None
    except Exception as e:
        print(f"Error: Unexpected error querying {host}:{port} - {e}")
        return None


def get_p2pool_stats(miner_address: str, network: str = "main") -> Tuple[str, int, str, int, int, int]:
    """
    Queries the p2pool.observer API for a miner's stats.
    Calculates active shares by checking recent shares against the PPLNS window.
    
    Args:
        miner_address: The Monero wallet address
        network: P2Pool network (main, mini, or nano)
        
    Returns:
        Tuple of (blocks_found, shares_held, payouts_sent, active_shares, active_uncles, total_shares)
    """
    if not miner_address:
        return None, None, None, None, None, None

    base_url = config.P2POOL_NETWORKS.get(network, config.P2POOL_NETWORKS["main"])
    
    try:
        # 1. Get Miner Info for Total Shares (Index 1)
        info_url = f"{base_url}api/miner_info/{miner_address}"
        info_resp = requests.get(info_url, timeout=config.P2POOL_API_TIMEOUT)
        info_resp.raise_for_status()
        info_data = info_resp.json()
        
        shares_data = info_data.get('shares', [])
        total_shares = 0
        total_uncles = 0
        if len(shares_data) > 1:
            total_shares = shares_data[1].get('shares', 0)
            total_uncles = shares_data[1].get('uncles', 0)
        
        # 2. Get Pool Height for Window Calculation
        window_size = config.P2POOL_WINDOW_SIZE
        
        # Get latest share height on the network
        last_share_url = f"{base_url}api/shares?limit=1"
        ls_resp = requests.get(last_share_url, timeout=config.P2POOL_API_TIMEOUT)
        ls_resp.raise_for_status()
        ls_data = ls_resp.json()
        
        if not ls_data:
            print(f"Warning: No shares found on {network} network")
            return "N/A", total_shares, "N/A", 0, 0, total_shares
            
        current_height = ls_data[0].get('side_height', 0)
        
        # 3. Get Miner's Recent Shares to count active ones
        miner_shares_url = f"{base_url}api/shares?miner={miner_address}"
        ms_resp = requests.get(miner_shares_url, timeout=config.P2POOL_API_TIMEOUT)
        ms_resp.raise_for_status()
        miner_shares = ms_resp.json()
        
        active_shares = 0
        active_uncles = 0
        window_start = current_height - window_size
        
        for share in miner_shares:
            if share.get('side_height', 0) >= window_start:
                active_shares += 1
            else:
                # Shares are sorted by height desc, so we can stop
                break

        blocks_found = "N/A"
        payouts_sent = "N/A"

        return blocks_found, total_shares, payouts_sent, active_shares, active_uncles, total_shares
        
    except requests.exceptions.Timeout:
        print(f"Warning: Timeout querying P2Pool API for {network} network")
        return None, None, None, None, None, None
    except requests.exceptions.RequestException as e:
        print(f"Warning: Error querying P2Pool API: {e}")
        return None, None, None, None, None, None
    except Exception as e:
        print(f"Error: Unexpected error processing P2Pool data from {base_url}: {e}")
        return None, None, None, None, None, None


def get_system_status(host: str, port: int, p2pool_miner_address: Optional[str] = None, 
                     p2pool_network: str = "main"):
    """
    Checks a single host and stores the status in the database.
    
    Args:
        host: Hostname or IP to check
        port: Miner API port
        p2pool_miner_address: Optional P2Pool wallet address
        p2pool_network: P2Pool network type
    """
    print(f"Checking {host}...")
    hashrate = get_monero_hashrate(host, port)
    
    cpu_usage = None
    ram_usage = None

    # Only get system stats for localhost
    if host == "127.0.0.1" or host == "localhost":
        try:
            cpu_usage = psutil.cpu_percent(interval=1)
            ram_usage = psutil.virtual_memory().percent
        except Exception as e:
            print(f"Warning: Could not get system stats: {e}")

    # Store in database
    try:
        db.upsert_miner(host, hashrate, cpu_usage, ram_usage)
        
        if hashrate is not None:
            print(f"  ✓ Online - Hashrate: {hashrate:.2f} H/s")
            if cpu_usage is not None:
                print(f"  CPU: {cpu_usage:.1f}% | RAM: {ram_usage:.1f}%")
        else:
            print(f"  ✗ Offline or unreachable")
    except Exception as e:
        print(f"Error: Failed to store miner data: {e}")

    # Handle P2Pool stats if requested
    if p2pool_miner_address:
        print(f"Fetching P2Pool stats for {p2pool_network} network...")
        blocks, shares_24h, payouts, window, uncles, total = get_p2pool_stats(
            p2pool_miner_address, p2pool_network
        )
        
        if blocks is not None:
            try:
                db.upsert_p2pool_stats(
                    p2pool_miner_address, blocks, shares_24h, payouts, 
                    window, uncles, total
                )
                print(f"  Active Shares: {window} | Total: {total}")
            except Exception as e:
                print(f"Error: Failed to store P2Pool data: {e}")


def scan_network(network_range: str, port: int):
    """
    Scans a given network range for miners and stores results.
    
    Args:
        network_range: CIDR notation network range (e.g., 192.168.1.0/24)
        port: Miner API port
    """
    try:
        network = ipaddress.ip_network(network_range)
    except ValueError as e:
        print(f"Error: Invalid network range '{network_range}'. Please use CIDR notation (e.g., 192.168.1.0/24).")
        print(f"Details: {e}")
        return

    total_hosts = network.num_addresses - 2  # Exclude network and broadcast
    print(f"Scanning {total_hosts} hosts in {network_range}...")
    
    found = 0
    for i, ip in enumerate(network.hosts(), 1):
        print(f"[{i}/{total_hosts}] Checking {ip}...", end='\r')
        hashrate = get_monero_hashrate(host=str(ip), port=port)
        
        try:
            db.upsert_miner(str(ip), hashrate)
            if hashrate is not None:
                found += 1
                print(f"\n  ✓ Found miner at {ip} - {hashrate:.2f} H/s")
        except Exception as e:
            print(f"\nError: Failed to store data for {ip}: {e}")
    
    print(f"\nScan complete. Found {found} active miner(s).")


def cleanup_database():
    """Cleanup old records from the database."""
    print(f"Cleaning up data older than {config.DATA_RETENTION_DAYS} days...")
    try:
        db.cleanup_old_data()
        print("Cleanup complete.")
    except Exception as e:
        print(f"Error during cleanup: {e}")


def show_database_stats():
    """Display database statistics."""
    try:
        stats = db.get_database_stats()
        print("\n=== Database Statistics ===")
        print(f"Total Miners: {stats['total_miners']}")
        print(f"Online Miners: {stats['online_miners']}")
        print(f"History Records: {stats['history_records']}")
        print(f"P2Pool Miners: {stats['p2pool_miners']}")
        print("===========================\n")
    except Exception as e:
        print(f"Error retrieving database stats: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""Sentinel Probe: A tool for monitoring system status, Monero miners, and network security.
        
Modes of Operation:
  1. Host Check:   Get status for a single host and store in local database.
  2. Network Scan: Scan a network range for active miners.
  3. NIDS Mode:    Run the Network Intrusion Detection System. (Requires root)
  4. Maintenance:  Database cleanup and statistics.
        """,
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    # Mode-switching arguments
    parser.add_argument("--host", help="Mode 1: Hostname or IP of the miner to check.")
    parser.add_argument("--scan", dest="scan_range", 
                       help="Mode 2: Scan a network in CIDR notation (e.g., 192.168.1.0/24).")
    
    nids_group = parser.add_argument_group("Mode 3: NIDS (Requires Root)")
    nids_group.add_argument("--nids", action="store_true", 
                           help="Run the Network Intrusion Detection System.")
    nids_group.add_argument("--iface", 
                           help="Specify network interface for NIDS (e.g., eth0, wlan0).")

    maintenance_group = parser.add_argument_group("Mode 4: Maintenance")
    maintenance_group.add_argument("--cleanup", action="store_true",
                                  help="Clean up old data from the database.")
    maintenance_group.add_argument("--stats", action="store_true",
                                  help="Show database statistics.")

    # General arguments
    parser.add_argument("--port", type=int, default=config.DEFAULT_MINER_PORT,
                       help=f"API port for the Monero miner(s). Default: {config.DEFAULT_MINER_PORT}.")
    parser.add_argument("--p2pool-miner-address", 
                       help="The Monero address of your p2pool miner.")
    parser.add_argument("--p2pool-network", choices=["main", "mini", "nano"], 
                       default="main",
                       help="The p2pool network to query (main, mini, or nano). Default: main.")
    
    args = parser.parse_args()

    # Execute the chosen mode
    if args.stats:
        show_database_stats()
        
    elif args.cleanup:
        cleanup_database()
        
    elif args.nids:
        if not NIDS_AVAILABLE:
            print("Error: The 'scapy' library is not installed. NIDS mode is unavailable.")
            print("Please run: pip install scapy")
            sys.exit(1)
        else:
            print("--- Starting NIDS Mode ---")
            start_nids_sniffer(interface=args.iface)
            
    elif args.scan_range:
        print(f"--- Starting Network Scan on {args.scan_range} ---")
        scan_network(args.scan_range, args.port)
        print("--- Scan Complete ---")

    elif args.host:
        print(f"--- Checking Host: {args.host} ---")
        get_system_status(args.host, args.port, args.p2pool_miner_address, args.p2pool_network)
        print("--- Check Complete ---")

    else:
        parser.print_help()
        sys.exit(1)
