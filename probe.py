import psutil
import datetime
import requests
import argparse
import ipaddress
import threading
from queue import Queue

import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
try:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("Successfully connected to Firebase.")
except Exception as e:
    db = None
    print(f"Warning: Could not connect to Firebase. {e}")


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
        
    doc_ref.set(data, merge=True)


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
    hashrate_str = f"{hashrate:.2f} H/s" if hashrate is not None else "Offline"
    
    cpu_usage = None
    ram_usage = None

    if host == "127.0.0.1":
        # Local stats
        cpu_usage = psutil.cpu_percent(interval=1)
        ram_usage = psutil.virtual_memory().percent
        print(f"[{datetime.datetime.now()}] Host: {host} | CPU: {cpu_usage}% | RAM: {ram_usage}% | Hashrate: {hashrate_str}")
    else:
        # Remote stats
        print(f"[{datetime.datetime.now()}] Host: {host} | Hashrate: {hashrate_str}")

    # Push to cloud
    push_to_firebase(host, hashrate, cpu_usage, ram_usage)


def worker(task_queue, results_queue, port):
    """Pulls an IP from the queue, gets hashrate, and pushes to cloud."""
    while not task_queue.empty():
        ip = task_queue.get()
        hashrate = get_monero_hashrate(host=str(ip), port=port)
        
        # Push to cloud for every scanned host
        push_to_firebase(str(ip), hashrate)
        
        if hashrate is not None:
            results_queue.put((str(ip), hashrate))
        task_queue.task_done()


def scan_network(network_range, port):
    """Scans a given network range for miners and prints a summary."""
    try:
        network = ipaddress.ip_network(network_range)
    except ValueError:
        print(f"Error: Invalid network range '{network_range}'. Please use CIDR notation (e.g., 192.168.1.0/24).")
        return

    print(f"Scanning {network.num_addresses} addresses on port {port}...")

    task_queue = Queue()
    results_queue = Queue()

    for ip in network.hosts():
        task_queue.put(ip)

    threads = []
    num_threads = min(network.num_addresses, 50) # Use up to 50 threads

    for _ in range(num_threads):
        thread = threading.Thread(target=worker, args=(task_queue, results_queue, port))
        thread.start()
        threads.append(thread)

    task_queue.join() # Block until all tasks are processed

    for thread in threads:
        thread.join()

    print("\n--- Scan Complete ---")
    if results_queue.empty():
        print("No active miners found.")
    else:
        print(f"{'IP Address':<20} {'Hashrate':<20}")
        print("-" * 40)
        while not results_queue.empty():
            ip, hashrate = results_queue.get()
            print(f"{ip:<20} {hashrate:<20.2f} H/s")
    print("---------------------")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="System and Monero miner status probe.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--host", help="Hostname or IP address of the miner to check.")
    group.add_argument("--scan", dest="scan_range", help="Scan a network range in CIDR notation (e.g., 192.168.1.0/24).")
    parser.add_argument("--port", type=int, default=8000, help="API port of the miner(s). Defaults to 8000.")
    args = parser.parse_args()
    
    if args.scan_range:
        scan_network(args.scan_range, args.port)
    else: # args.host must be present
        get_system_status(args.host, args.port)
