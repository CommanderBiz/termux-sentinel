#!/usr/bin/env python3
"""
Network Intrusion Detection System (NIDS) for Sentinel.
Monitors network traffic for security threats and stores alerts in local database.
"""

from scapy.all import sniff, ARP
import datetime
import argparse
import sys

# --- Configuration ---
from database import SentinelDB

# Initialize database
db = SentinelDB()

# In-memory store to track MAC addresses for IPs
arp_table = {}


def push_alert(alert_type: str, details: str, severity: str = "medium", 
               source_ip: str = None, source_mac: str = None):
    """
    Stores a security alert in the local database.
    
    Args:
        alert_type: Type of security alert (e.g., "ARP Spoofing")
        details: Detailed description of the alert
        severity: Alert severity level (low, medium, high, critical)
        source_ip: Source IP address if applicable
        source_mac: Source MAC address if applicable
    """
    try:
        db.add_alert(alert_type, details, severity, source_ip, source_mac)
        print(f"NIDS: Successfully stored '{alert_type}' alert in database.")
    except Exception as e:
        print(f"NIDS: ERROR storing alert: {e}")


def arp_spoof_detector(packet):
    """
    Analyzes ARP packets to detect potential ARP spoofing attacks.
    
    ARP spoofing is detected when:
    - An IP address that was previously associated with one MAC address
      suddenly appears with a different MAC address
    
    This can indicate:
    - Legitimate device replacement/update
    - DHCP reassignment
    - Man-in-the-middle attack attempt (ARP spoofing)
    """
    if ARP in packet and packet[ARP].op in (1, 2):  # ARP Request or Reply
        src_ip = packet[ARP].psrc
        src_mac = packet[ARP].hwsrc

        if src_ip in arp_table and arp_table[src_ip] != src_mac:
            # Potential ARP spoofing detected! Check DB to prevent spam
            entry = db.get_arp_entry(src_ip, src_mac)
            
            # Check if we should alert (if we have never alerted, or if it's been > 24 hours)
            should_alert = True
            if entry and entry.get('last_alerted'):
                try:
                    last_alerted_str = entry['last_alerted']
                    last_alerted = datetime.datetime.fromisoformat(last_alerted_str.replace('Z', '+00:00'))
                    time_since_alert = datetime.datetime.now(datetime.timezone.utc) - last_alerted
                    if time_since_alert.total_seconds() < 86400: # 24 hours
                        should_alert = False
                except Exception as e:
                    print(f"NIDS: Error parsing timestamp: {e}")
            
            if should_alert:
                alert_details = (
                    f"Potential ARP Spoofing Detected!\n"
                    f"IP Address: {src_ip}\n"
                    f"Previous MAC: {arp_table[src_ip]}\n"
                    f"New MAC (Suspicious): {src_mac}\n\n"
                    f"This could indicate:\n"
                    f"- Man-in-the-middle attack attempt\n"
                    f"- Legitimate device change\n"
                    f"- DHCP reassignment\n\n"
                    f"Recommended Action: Investigate this host immediately."
                )
                
                print(f"\n{'='*60}")
                print(f"🚨 NIDS SECURITY ALERT 🚨")
                print(f"{'='*60}")
                print(alert_details)
                print(f"{'='*60}\n")
                
                # Store alert in database with high severity
                push_alert(
                    alert_type="ARP Spoofing",
                    details=alert_details,
                    severity="high",
                    source_ip=src_ip,
                    source_mac=src_mac
                )
            
            # Record/Update the entry in the DB, marking alerted state
            db.update_arp_entry(src_ip, src_mac, alerted=should_alert)
        else:
            # Normal ARP traffic, log it quietly to history
            db.update_arp_entry(src_ip, src_mac, alerted=False)
        
        # Update the memory ARP table with the latest mapping
        arp_table[src_ip] = src_mac


def start_nids_sniffer(interface=None):
    """
    Starts the network sniffer to monitor for security threats.
    
    Args:
        interface: Network interface to monitor (e.g., eth0, wlan0)
                  If None, Scapy will attempt to select the best interface
    
    Note:
        This function requires root/administrator privileges to capture packets.
    """
    print("="*60)
    print("🛡️  SENTINEL NIDS - Network Intrusion Detection System")
    print("="*60)
    print(f"Starting network sniffer...")
    
    if interface:
        print(f"Monitoring interface: {interface}")
    else:
        print(f"Monitoring default interface (auto-detected)")
    
    print(f"Detection modes enabled:")
    print(f"  ✓ ARP Spoofing Detection")
    print(f"  ✓ Alert logging to SQLite database")
    print(f"\nPress Ctrl+C to stop monitoring...")
    print("="*60 + "\n")
    
    try:
        # Monitor ARP traffic for spoofing attacks
        # We can add more filters and detection methods here later
        sniff(
            filter="arp",
            prn=arp_spoof_detector,
            store=0,
            iface=interface
        )
        print("\nNIDS: Sniffer stopped gracefully.")
        
    except PermissionError:
        print("\n❌ ERROR: Permission denied.")
        print("NIDS requires root/administrator privileges to capture network packets.")
        print("Please run with: sudo python3 nids.py")
        sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n\n⏹  NIDS monitoring stopped by user.")
        print("All alerts have been saved to the database.")
        
    except Exception as e:
        print(f"\n❌ NIDS: An error occurred: {e}")
        print("Please ensure:")
        print("  1. You are running with root privileges (sudo)")
        print("  2. The network interface exists and is active")
        print("  3. Scapy is properly installed (pip install scapy)")
        sys.exit(1)


def view_recent_alerts(limit=10):
    """Display recent alerts from the database."""
    try:
        alerts = db.get_alerts(limit=limit)
        
        if not alerts:
            print("No alerts found in database.")
            return
        
        print(f"\n{'='*60}")
        print(f"📋 Recent Security Alerts (Last {limit})")
        print(f"{'='*60}\n")
        
        for alert in alerts:
            ack_status = "✓ Acknowledged" if alert['acknowledged'] else "⚠ New"
            severity_emoji = {
                'low': '🟢',
                'medium': '🟡',
                'high': '🔴',
                'critical': '🔴🔴'
            }.get(alert['severity'], '⚪')
            
            print(f"{severity_emoji} Alert ID: {alert['id']} - {ack_status}")
            print(f"   Type: {alert['type']}")
            print(f"   Time: {alert['timestamp']}")
            print(f"   Severity: {alert['severity'].upper()}")
            
            if alert['source_ip']:
                print(f"   Source IP: {alert['source_ip']}")
            if alert['source_mac']:
                print(f"   Source MAC: {alert['source_mac']}")
            
            print(f"   Details: {alert['details'][:100]}...")
            print()
        
    except Exception as e:
        print(f"Error retrieving alerts: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""Sentinel NIDS - Network Intrusion Detection System
        
Monitors network traffic for security threats including:
  • ARP Spoofing attacks
  • Suspicious network behavior
  
All alerts are stored in the local SQLite database for review in the dashboard.
        """,
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument(
        "--iface",
        help="Network interface to monitor (e.g., eth0, wlan0, enp0s3)"
    )
    
    parser.add_argument(
        "--view-alerts",
        action="store_true",
        help="View recent alerts from the database instead of starting monitoring"
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of alerts to display when using --view-alerts (default: 10)"
    )
    
    args = parser.parse_args()
    
    if args.view_alerts:
        view_recent_alerts(limit=args.limit)
    else:
        print("NOTE: This script requires root privileges to capture network packets.")
        print("If you get permission errors, run with: sudo python3 nids.py\n")
        start_nids_sniffer(interface=args.iface)
