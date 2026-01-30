#!/usr/bin/env python3
"""
Report Generator for Sentinel Monitoring System.
Generates comprehensive reports by running probe.py and querying the database.
"""

import argparse
import subprocess
import os
import sys
from datetime import datetime
from database import SentinelDB


def print_header(title):
    """Print a formatted header."""
    width = 70
    print("\n" + "="*width)
    print(f" {title.center(width-2)} ")
    print("="*width + "\n")


def generate_database_report():
    """Generate a report from the current database state."""
    try:
        db = SentinelDB()
        
        print_header("SENTINEL DATABASE REPORT")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Get database statistics
        stats = db.get_database_stats()
        
        print("📊 System Overview:")
        print(f"  Total Miners Discovered: {stats['total_miners']}")
        print(f"  Currently Online: {stats['online_miners']}")
        print(f"  Historical Records: {stats['history_records']}")
        print(f"  P2Pool Miners: {stats['p2pool_miners']}")
        print(f"  Unacknowledged Alerts: {stats['unacknowledged_alerts']}")
        
        # Get miner details
        miners = db.get_all_miners()
        
        if miners:
            print("\n" + "-"*70)
            print("⛏️  MINER STATUS DETAILS")
            print("-"*70 + "\n")
            
            for miner in miners:
                status_icon = "✅" if miner['status'] == 'Online' else "❌"
                print(f"{status_icon} {miner['host']}")
                print(f"   Status: {miner['status']}")
                print(f"   Last Seen: {miner['last_seen']}")
                
                if miner['status'] == 'Online':
                    hashrate = miner.get('hashrate', 0) or 0
                    print(f"   Hashrate: {hashrate:.2f} H/s")
                    
                    if miner.get('cpu_usage') is not None:
                        print(f"   CPU: {miner['cpu_usage']:.1f}%")
                    if miner.get('ram_usage') is not None:
                        print(f"   RAM: {miner['ram_usage']:.1f}%")
                print()
        
        # Get P2Pool stats
        p2pool_stats = db.get_all_p2pool_stats()
        
        if p2pool_stats:
            print("-"*70)
            print("🏊 P2POOL STATISTICS")
            print("-"*70 + "\n")
            
            for stat in p2pool_stats:
                print(f"Miner Address: {stat['miner_address']}")
                print(f"  Active Shares: {stat.get('active_shares', 0)}")
                print(f"  Total Shares: {stat.get('total_shares', 0)}")
                print(f"  Active Uncles: {stat.get('active_uncles', 0)}")
                print(f"  Last Updated: {stat['last_seen']}")
                print()
        
        # Get recent alerts
        alerts = db.get_alerts(acknowledged=False, limit=10)
        
        if alerts:
            print("-"*70)
            print("🚨 RECENT SECURITY ALERTS (Unacknowledged)")
            print("-"*70 + "\n")
            
            for alert in alerts:
                severity_emoji = {
                    'low': '🟢',
                    'medium': '🟡',
                    'high': '🔴',
                    'critical': '🔴🔴'
                }.get(alert['severity'], '⚪')
                
                print(f"{severity_emoji} Alert ID {alert['id']} - {alert['type']}")
                print(f"   Severity: {alert['severity'].upper()}")
                print(f"   Time: {alert['timestamp']}")
                
                if alert['source_ip']:
                    print(f"   Source: {alert['source_ip']}")
                
                # Print first 150 chars of details
                details = alert['details']
                if len(details) > 150:
                    details = details[:150] + "..."
                print(f"   Details: {details}")
                print()
        
        print("="*70)
        print(f"End of Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"❌ Error generating database report: {e}")
        sys.exit(1)


def run_probe_scan(host=None, scan_range=None, port=8000, p2pool_address=None):
    """
    Execute probe.py to scan miners and update the database.
    
    Args:
        host: Single host to check
        scan_range: Network range to scan
        port: Miner API port
        p2pool_address: P2Pool miner address for stats
    """
    script_path = os.path.join(os.path.dirname(__file__), "probe.py")
    
    if not os.path.exists(script_path):
        print(f"❌ Error: probe.py not found at {script_path}")
        sys.exit(1)
    
    command = ["python3", script_path]
    
    if host:
        command.extend(["--host", host])
    elif scan_range:
        command.extend(["--scan", scan_range])
    else:
        print("❌ Error: Either --host or --scan must be provided.")
        sys.exit(1)

    command.extend(["--port", str(port)])
    
    if p2pool_address:
        command.extend(["--p2pool-miner-address", p2pool_address])

    try:
        print_header("RUNNING PROBE SCAN")
        print(f"Command: {' '.join(command)}\n")
        
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        
        print("✅ Probe scan completed successfully.\n")
        
        if result.stdout:
            print("Scan Output:")
            print("-" * 70)
            print(result.stdout)
            print("-" * 70)
        
        if result.stderr:
            print("\nWarnings/Errors:")
            print("-" * 70)
            print(result.stderr)
            print("-" * 70)
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running probe scan: {e}")
        if e.stdout:
            print(f"\nStdout:\n{e.stdout}")
        if e.stderr:
            print(f"\nStderr:\n{e.stderr}")
        sys.exit(1)
        
    except FileNotFoundError:
        print(f"❌ Error: Python3 not found. Please ensure Python is installed.")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""Sentinel Report Generator
        
Generates comprehensive reports by:
1. Running probe.py to collect current data (optional)
2. Querying the database for historical and current stats
3. Displaying miner status, P2Pool stats, and security alerts

Usage Examples:
  # Generate report from current database
  python3 report_generator.py --report-only
  
  # Scan a host first, then generate report
  python3 report_generator.py --host 192.168.1.100
  
  # Scan network first, then generate report
  python3 report_generator.py --scan 192.168.1.0/24
  
  # Full scan with P2Pool stats and report
  python3 report_generator.py --host 127.0.0.1 --p2pool-address YOUR_ADDRESS
        """,
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument(
        "--host",
        help="Hostname or IP address of the miner to check before generating report"
    )
    
    parser.add_argument(
        "--scan",
        dest="scan_range",
        help="Scan a network range in CIDR notation (e.g., 192.168.1.0/24)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="API port of the miner(s). Default: 8000"
    )
    
    parser.add_argument(
        "--p2pool-address",
        help="P2Pool miner address to include in scan"
    )
    
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Generate report from existing database without running new scan"
    )
    
    args = parser.parse_args()
    
    # Run probe scan if requested
    if not args.report_only:
        if args.host or args.scan_range:
            run_probe_scan(
                host=args.host,
                scan_range=args.scan_range,
                port=args.port,
                p2pool_address=args.p2pool_address
            )
        else:
            print("❌ Error: Specify --host, --scan, or --report-only")
            parser.print_help()
            sys.exit(1)
    
    # Generate report from database
    generate_database_report()
