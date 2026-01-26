#!/usr/bin/env python3

import psutil
import datetime
import requests
import argparse
import ipaddress

# --- Local Imports ---
# This will allow us to run the NIDS as part of the probe
try:
    from nids import start_nids_sniffer
    NIDS_AVAILABLE = True
except ImportError:
    NIDS_AVAILABLE = False
    def start_nids_sniffer(interface=None):
        print("Probe: NIDS module not found. Skipping.")

import firebase_admin
from firebase_admin import credentials, firestore

# --- Firebase Initialization ---
db = None
def initialize_firebase():
    """Initializes the Firebase connection if not already done."""
    global db
    if firebase_admin._apps: # Clear existing apps if any
        del firebase_admin._apps[firebase_admin._DEFAULT_APP_NAME]
    try:
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
        db = firestore.client()
    except Exception as e:
        db = None

def push_to_firebase(host, hashrate, cpu=None, ram=None):
    """Pushes stats to the Firestore 'miners' collection."""
    if not db:
        return # Do nothing if Firebase is not connected

    doc_ref = db.collection("miners").document(host)
    data = {
        "last_seen": datetime.datetime.now(datetime.timezone.utc),
        "hashrate": hashrate,
        "status": "Online" if hashrate is not None else "Offline"
    }
    if cpu is not None:
        data["cpu_usage"] = cpu
    if ram is not None:
        data["ram_usage"] = ram
        
    try:
        doc_ref.set(data, merge=True)
    except Exception as e:
        pass # Silently fail for now, or log to a file if needed in the future


def get_monero_hashrate(host="127.0.0.1", port=8000):
    """
    Queries the miner's API for the current hashrate.
    Returns the hashrate in H/s, or None if an error occurs.
    """
    api_url = f"http://{host}:{port}/2/summary"
    try:
        response = requests.get(api_url, timeout=2) # Shorter timeout for scanning
        response.raise_for_status()
        data = response.json()
        hashrate = data.get("hashrate", {}).get("total", [0])[0]
        return hashrate
    except requests.exceptions.RequestException:
        return None


def get_p2pool_stats(miner_address, network="main"):
    """
    Queries the p2pool.observer API for a miner's stats using /api/miner_info/<address>.
    """
    if not miner_address:
        return None, None, None

    base_urls = {
        "main": "https://p2pool.observer/",
        "mini": "https://mini.p2pool.observer/",
        "nano": "https://nano.p2pool.observer/",
    }
    base_url = base_urls.get(network, "https://p2pool.observer/")
    api_url = f"{base_url}api/miner_info/{miner_address}"

    try:
        response = requests.get(api_url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        # Correctly parse the new data structure
        shares_held = data.get('shares', [{}, {'shares': 'N/A'}])[1].get('shares')
        blocks_found = "N/A"  # Not available in this endpoint
        payouts_sent = "N/A" # Not available in this endpoint

        return blocks_found, shares_held, payouts_sent
    except (requests.exceptions.RequestException, IndexError) as e:
        print(f"P2Pool: Error processing data from {base_url}: {e}")
        return None, None, None


def push_p2pool_to_firebase(miner_address, blocks_found, shares_held, payouts_sent):
    """Pushes p2pool stats to the Firestore 'p2pool' collection."""
    if not db:
        return

    doc_ref = db.collection("p2pool").document(miner_address)
    data = {
        "last_seen": datetime.datetime.now(datetime.timezone.utc),
        "blocks_found": blocks_found,
        "shares_held": shares_held,
        "payouts_sent": payouts_sent
    }
    try:
        doc_ref.set(data, merge=True)
    except Exception as e:
        pass # Silently fail



def get_system_status(host, port, p2pool_miner_address=None, p2pool_network="main"):
    """Checks a single host and prints/pushes the status."""
    hashrate = get_monero_hashrate(host, port)
    
    cpu_usage = None
    ram_usage = None

    if host == "127.0.0.1":
        # Local stats
        cpu_usage = psutil.cpu_percent(interval=1)
        ram_usage = psutil.virtual_memory().percent
    else:
        # Remote stats
        pass

    # Push to cloud
    push_to_firebase(host, hashrate, cpu_usage, ram_usage)

    if p2pool_miner_address:
        blocks, shares, payouts = get_p2pool_stats(p2pool_miner_address, p2pool_network)
        if blocks is not None:
            push_p2pool_to_firebase(p2pool_miner_address, blocks, shares, payouts)


def scan_network(network_range, port):
    """Scans a given network range for miners and prints a summary."""
    try:
        network = ipaddress.ip_network(network_range)
    except ValueError:
        print(f"Error: Invalid network range '{network_range}'. Please use CIDR notation (e.g., 192.168.1.0/24).")
        return

    for ip in network.hosts():
        hashrate = get_monero_hashrate(host=str(ip), port=port)
        push_to_firebase(str(ip), hashrate)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""Sentinel Probe: A tool for monitoring system status, Monero miners, and network security.
        
        Modes of Operation:
        1. Host Check:   Get status for a single host.
        2. Network Scan: Scan a network range for active miners.
        3. NIDS Mode:    Run the Network Intrusion Detection System. (Requires root)
        """,
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    # Mode-switching arguments
    parser.add_argument("--host", help="Mode 1: Hostname or IP of the miner to check.")
    parser.add_argument("--scan", dest="scan_range", help="Mode 2: Scan a network in CIDR notation (e.g., 192.168.1.0/24).")
    
    nids_group = parser.add_argument_group("Mode 3: NIDS (Requires Root)")
    nids_group.add_argument("--nids", action="store_true", help="Run the Network Intrusion Detection System.")
    nids_group.add_argument("--iface", help="Specify network interface for NIDS (e.g., eth0, wlan0).")

    # General arguments
    parser.add_argument("--port", type=int, default=8000, help="API port for the Monero miner(s). Default: 8000.")
    parser.add_argument("--p2pool-miner-address", help="The Monero address of your p2pool miner.")
    parser.add_argument("--p2pool-network", choices=["main", "mini", "nano"], default="main", help="The p2pool network to query (main, mini, or nano). Default: main.")
    
    args = parser.parse_args()
    
    # Initialize Firebase for all modes that need it
    if args.host or args.scan_range or args.nids:
        initialize_firebase()

    # Execute the chosen mode
    if args.nids:
        if not NIDS_AVAILABLE:
            print("Error: The 'scapy' library is not installed. NIDS mode is unavailable.")
            print("Please run: pip install scapy")
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
        exit(1)