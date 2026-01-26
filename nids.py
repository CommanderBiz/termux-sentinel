#!/usr/bin/env python3

from scapy.all import sniff, ARP
import datetime

import firebase_admin
from firebase_admin import credentials, firestore

# --- Firebase Initialization (similar to probe.py) ---
try:
    # This assumes serviceAccountKey.json is in the same directory
    cred = credentials.Certificate("serviceAccountKey.json")
    # Avoid re-initializing if it's already done by another script
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    db = None
    print(f"NIDS: Warning: Could not connect to Firebase. {e}")
# ---------------------------------------------------------


def push_alert_to_firebase(alert_type, details):
    """Pushes a security alert to the Firestore 'alerts' collection."""
    if not db:
        print(f"NIDS: Firebase DB not connected. Skipping alert: {alert_type}")
        return

    doc_ref = db.collection("alerts").document()
    data = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc),
        "type": alert_type,
        "details": details,
        "acknowledged": False # For future use in the dashboard
    }
    try:
        doc_ref.set(data)
        print(f"NIDS: Successfully pushed '{alert_type}' alert to Firebase.")
    except Exception as e:
        print(f"NIDS: ERROR pushing alert: {e}")


# --- Intrusion Detection Logic ---

# In-memory store to track MAC addresses for IPs
arp_table = {}

def arp_spoof_detector(packet):
    """
    Analyzes ARP packets to detect potential ARP spoofing attacks.
    """
    if ARP in packet and packet[ARP].op in (1, 2): # ARP Request or Reply
        src_ip = packet[ARP].psrc
        src_mac = packet[ARP].hwsrc

        if src_ip in arp_table and arp_table[src_ip] != src_mac:
            # Potential ARP spoofing!
            alert_details = (
                f"Potential ARP Spoofing Detected!\n"
                f"IP Address: {src_ip}\n"
                f"Original MAC: {arp_table[src_ip]}\n"
                f"New (Suspicious) MAC: {src_mac}"
            )
            print(f"\n--- NIDS ALERT ---\n{alert_details}\n------------------\n")
            push_alert_to_firebase("ARP Spoofing", alert_details)
        
        # Update the table with the latest mapping
        arp_table[src_ip] = src_mac


def start_nids_sniffer(interface=None):
    """
    Starts the network sniffer to monitor for threats.
    
    Args:
        interface (str, optional): The network interface to sniff on. 
                                   If None, Scapy will try to find the best one.
    """
    print("NIDS: Starting network sniffer...")
    try:
        # We can add more filters and handlers here later
        sniff(filter="arp", prn=arp_spoof_detector, store=0, iface=interface)
        print("NIDS: Sniffer stopped.")
    except Exception as e:
        print(f"NIDS: An error occurred with the sniffer: {e}")
        print("NIDS: Please ensure you are running this script with root privileges.")


if __name__ == "__main__":
    # This allows running the NIDS independently for testing
    print("Running NIDS in standalone mode (for testing).")
    print("NOTE: This requires root privileges to capture network packets.")
    # You might need to specify the interface, e.g., "eth0" or "wlan0"
    start_nids_sniffer()
