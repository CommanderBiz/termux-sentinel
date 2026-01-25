#!/usr/bin/env python3

import psutil
import datetime
import requests
import argparse
import ipaddress

import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
try:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    # print("Successfully connected to Firebase.") # Removed debug
except Exception as e:
    db = None
    # print(f"Warning: Could not connect to Firebase. {e}") # Removed debug


def push_to_firebase(host, hashrate, cpu=None, ram=None):
    """Pushes stats to the Firestore 'miners' collection."""
    if not db:
        # print(f"[{datetime.datetime.now()}] FIREBASE: DB not connected. Skipping push for {host}.") # Removed debug
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
        # print(f"[{datetime.datetime.now()}] FIREBASE: Successfully pushed update for {host}.") # Removed debug
    except Exception as e:
        # print(f"[{datetime.datetime.now()}] FIREBASE: ERROR pushing for {host}: {e}") # Removed debug
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


def get_system_status(host, port):
    """Checks a single host and prints/pushes the status."""
    hashrate = get_monero_hashrate(host, port)
    # hashrate_str = f"{hashrate:.2f} H/s" if hashrate is not None else "Offline" # Removed debug
    
    cpu_usage = None
    ram_usage = None

    if host == "127.0.0.1":
        # Local stats
        cpu_usage = psutil.cpu_percent(interval=1)
        ram_usage = psutil.virtual_memory().percent
        # print(f"[{datetime.datetime.now()}] Host: {host} | CPU: {cpu_usage}% | RAM: {ram_usage}% | Hashrate: {hashrate_str}") # Removed debug
    else:
        # Remote stats
        # print(f"[{datetime.datetime.now()}] Host: {host} | Hashrate: {hashrate_str}") # Removed debug
        pass

    # Push to cloud
    push_to_firebase(host, hashrate, cpu_usage, ram_usage)


def scan_network(network_range, port):
    """Scans a given network range for miners and prints a summary."""
    try:
        network = ipaddress.ip_network(network_range)
    except ValueError:
        print(f"Error: Invalid network range '{network_range}'. Please use CIDR notation (e.g., 192.168.1.0/24).")
        return

    # print(f"[{datetime.datetime.now()}] SCAN: Starting sequential scan of {network_range}...") # Removed debug
    for ip in network.hosts():
        # print(f"[{datetime.datetime.now()}] SCAN: Checking {ip}") # Removed debug
        hashrate = get_monero_hashrate(host=str(ip), port=port)
        push_to_firebase(str(ip), hashrate)
    # print(f"[{datetime.datetime.now()}] SCAN: Finished sequential scan of {network_range}.") # Removed debug


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="System and Monero miner status probe.")
    parser.add_argument("--host", help="Hostname or IP address of the miner to check.")
    parser.add_argument("--scan", dest="scan_range", help="Scan a network range in CIDR notation (e.g., 192.168.1.0/24).")
    parser.add_argument("--port", type=int, default=8000, help="API port of the miner(s). Defaults to 8000.")
    args = parser.parse_args()
    
    if args.scan_range:
        scan_network(args.scan_range, args.port)
    elif args.host:
        get_system_status(args.host, args.port)
    else:
        parser.print_help()
        exit(1)