#!/usr/bin/env python3
"""
Sentinel Dashboard: Real-time monitoring dashboard for Monero miners and system stats.
Refactored version using local SQLite database.
"""

import streamlit as st
import pandas as pd
import datetime
from typing import Optional

# --- Configuration ---
import config
from database import SentinelDB

# Page configuration
st.set_page_config(
    page_title="Sentinel Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_resource
def get_database():
    """Get or create the database connection (cached)."""
    return SentinelDB()


def format_timestamp(timestamp_str: Optional[any]) -> str:
    """Format a timestamp string for display."""
    if not timestamp_str:
        return "Never"
    
    try:
        # Parse the timestamp
        if isinstance(timestamp_str, (int, float)):
            ts = datetime.datetime.fromtimestamp(timestamp_str, datetime.timezone.utc)
        elif isinstance(timestamp_str, str):
            # Remove timezone info if present for parsing
            timestamp_str = timestamp_str.replace('+00:00', '').replace('Z', '')
            ts = datetime.datetime.fromisoformat(timestamp_str)
        else:
            ts = timestamp_str
            
        # Calculate time ago
        now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        # Ensure ts is offset-naive for subtraction if now is offset-naive
        # But wait, datetime.now(utc) returns offset-aware? 
        # The original code: now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        # So it makes 'now' naive (UTC time).
        # We must make 'ts' naive as well if it isn't.
        if ts.tzinfo is not None:
             ts = ts.astimezone(datetime.timezone.utc).replace(tzinfo=None)
             
        delta = now - ts
        
        if delta.total_seconds() < 60:
            return "Just now"
        elif delta.total_seconds() < 3600:
            minutes = int(delta.total_seconds() / 60)
            return f"{minutes}m ago"
        elif delta.total_seconds() < 86400:
            hours = int(delta.total_seconds() / 3600)
            return f"{hours}h ago"
        else:
            days = int(delta.total_seconds() / 86400)
            return f"{days}d ago"
    except Exception as e:
        return "Unknown"


def display_security_alerts(db: SentinelDB):
    """Fetches and displays security alerts from the database."""
    st.subheader("🚨 Security Alerts")
    
    try:
        # Get unacknowledged alerts
        alerts = db.get_alerts(acknowledged=False, limit=50)
        
        if not alerts:
            st.success("✅ No active security alerts. Your network appears secure.")
            
            # Show option to view acknowledged alerts
            if st.checkbox("Show acknowledged alerts"):
                old_alerts = db.get_alerts(acknowledged=True, limit=20)
                if old_alerts:
                    st.info(f"Showing {len(old_alerts)} previously acknowledged alerts")
                    for alert in old_alerts:
                        display_single_alert(db, alert, show_actions=False)
            return
        
        # Show alert count
        col1, col2 = st.columns([3, 1])
        with col1:
            st.warning(f"⚠️ {len(alerts)} unacknowledged security alert(s)")
        with col2:
            if st.button("Acknowledge All"):
                db.acknowledge_all_alerts()
                st.success("All alerts acknowledged!")
                st.rerun()
        
        st.divider()
        
        # Display each alert
        for alert in alerts:
            display_single_alert(db, alert, show_actions=True)
            
    except Exception as e:
        st.error(f"Error loading security alerts: {e}")


def display_single_alert(db: SentinelDB, alert: dict, show_actions: bool = True):
    """Display a single security alert."""
    # Severity styling
    severity_config = {
        'low': ('🟢', 'info'),
        'medium': ('🟡', 'warning'),
        'high': ('🔴', 'error'),
        'critical': ('🔴🔴', 'error')
    }
    emoji, alert_type = severity_config.get(alert['severity'], ('⚪', 'info'))
    
    with st.container(border=True):
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.write(f"{emoji} **{alert['type']}** - {alert['severity'].upper()}")
            st.caption(f"Alert ID: {alert['id']} | {format_timestamp(alert['timestamp'])}")
        
        with col2:
            if show_actions:
                if st.button("✓ Ack", key=f"ack_{alert['id']}"):
                    db.acknowledge_alert(alert['id'])
                    st.rerun()
                if st.button("🗑️", key=f"del_{alert['id']}"):
                    db.delete_alert(alert['id'])
                    st.rerun()
        
        # Alert details
        if alert['source_ip']:
            st.write(f"**Source IP:** {alert['source_ip']}")
        if alert['source_mac']:
            st.write(f"**Source MAC:** {alert['source_mac']}")
        
        # Show details in expander
        with st.expander("View Details"):
            st.text(alert['details'])


def display_p2pool_stats(db: SentinelDB):
    """Fetches and displays P2Pool stats from the database."""
    st.subheader("🏊 P2Pool Stats")
    
    try:
        stats = db.get_all_p2pool_stats()
        
        if not stats:
            st.info("No P2Pool stats found. Run the probe with `--p2pool-miner-address` to see stats here.")
            return
        
        for stat in stats:
            with st.container(border=True):
                st.write(f"**Miner Address:** `{stat['miner_address']}`")
                st.caption(f"Last seen: {format_timestamp(stat.get('last_seen'))}")
                
                # First row: Shares and blocks
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Active Shares", 
                        stat.get("active_shares", 0),
                        help="Shares in current PPLNS window (2160 blocks)"
                    )
                with col2:
                    st.metric(
                        "Total Shares", 
                        stat.get("total_shares", 0),
                        help="All valid shares ever found"
                    )
                with col3:
                    st.metric(
                        "Active Uncles", 
                        stat.get("active_uncles", 0),
                        help="Uncle blocks in current PPLNS window"
                    )
                with col4:
                    blocks = stat.get("blocks_found", "N/A")
                    
                    # Safely convert to int for comparison
                    try:
                        blocks_int = int(blocks)
                    except (ValueError, TypeError):
                        blocks_int = 0
                        
                    if blocks != "N/A" and blocks_int > 0:
                        st.metric("Blocks Found", blocks, help="Blocks found by this miner 🎉")
                    else:
                        st.metric("Blocks Found", blocks if blocks != "N/A" else 0, help="Blocks found by this miner")
                
                # Second row: Payouts (prominent)
                st.divider()
                payouts = stat.get("payouts_sent", "N/A")
                last_amount = stat.get("last_payout_amount")
                last_time = stat.get("last_payout_time")
                total_amount = stat.get("total_payout_amount", 0)
                
                # Safely convert to int for comparison
                try:
                    payouts_int = int(payouts)
                except (ValueError, TypeError):
                    payouts_int = 0
                
                if payouts != "N/A" and payouts_int > 0:
                    col_p1, col_p2 = st.columns([1, 2])
                    with col_p1:
                        st.success(f"💰 **Total Payouts: {payouts}**")
                        if total_amount and total_amount > 0:
                            st.write(f"Total Amount: **{total_amount:.6f} XMR**")
                    with col_p2:
                        if last_amount is not None:
                            st.info(f"Last Payout: **{last_amount:.6f} XMR** ({format_timestamp(last_time)})")
                            
                elif payouts != "N/A" and payouts_int == 0:
                    st.info("💰 No payouts yet. Keep mining!")
                else:
                    st.info("💰 Payout data unavailable")
                    
    except Exception as e:
        st.error(f"Error loading P2Pool stats: {e}")


def display_miner_stats(db: SentinelDB, view_option: str):
    """Fetches and displays miner stats from the database."""
    st.subheader("⛏️ Miner Stats")
    
    try:
        online_only = (view_option == "Online Only")
        miners = db.get_all_miners(online_only=online_only)
        
        if not miners:
            if online_only:
                st.warning("No online miners found. Try selecting 'All Discovered Hosts' in the sidebar.")
            else:
                st.info("No miners discovered yet. Run the probe with `--host` or `--scan` to add miners.")
            return
        
        # Summary metrics at the top
        online_count = sum(1 for m in miners if m['status'] == 'Online')
        total_hashrate = sum(m.get('hashrate', 0) or 0 for m in miners if m['status'] == 'Online')
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Miners", len(miners))
        with col2:
            st.metric("Online Miners", online_count)
        with col3:
            st.metric("Total Hashrate", f"{total_hashrate:.2f} H/s")
        
        st.divider()
        
        # Display individual miners
        for miner in miners:
            status = miner.get("status", "Offline")
            
            with st.container(border=True):
                # Header row with host name and delete button
                col_header, col_delete = st.columns([5, 1])
                with col_header:
                    st.write(f"**Host:** {miner['host']}")
                    st.caption(f"Last seen: {format_timestamp(miner.get('last_seen'))}")
                with col_delete:
                    if st.button("🗑️", key=f"delete_{miner['host']}", help="Delete this host"):
                        # Delete from database
                        import sqlite3
                        conn = sqlite3.connect(config.DB_PATH)
                        cursor = conn.cursor()
                        cursor.execute('DELETE FROM miners WHERE host = ?', (miner['host'],))
                        cursor.execute('DELETE FROM miner_history WHERE host = ?', (miner['host'],))
                        conn.commit()
                        conn.close()
                        st.success(f"Deleted {miner['host']}")
                        st.rerun()
                
                # Stats row
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    if status == "Online":
                        hashrate = miner.get("hashrate", 0) or 0
                        st.success(f"✓ Online - Hashrate: {hashrate:.2f} H/s")
                    else:
                        st.error("✗ Offline")
                
                with col2:
                    cpu_usage = miner.get('cpu_usage')
                    if cpu_usage is not None:
                        st.metric("CPU Usage", f"{cpu_usage:.1f}%")
                    else:
                        st.metric("CPU Usage", "N/A")
                
                with col3:
                    ram_usage = miner.get('ram_usage')
                    if ram_usage is not None:
                        st.metric("RAM Usage", f"{ram_usage:.1f}%")
                    else:
                        st.metric("RAM Usage", "N/A")
                
                # Optional: Show history chart
                if st.checkbox(f"Show 24h history", key=f"history_{miner['host']}"):
                    display_miner_history(db, miner['host'])
                    
    except Exception as e:
        st.error(f"Error loading miner stats: {e}")


def display_miner_history(db: SentinelDB, host: str):
    """Display a chart of historical data for a miner."""
    try:
        history = db.get_miner_history(host, hours=24)
        
        if not history:
            st.info("No historical data available yet.")
            return
        
        # Convert to DataFrame for plotting
        df = pd.DataFrame(history)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')
        
        # Create charts
        col1, col2 = st.columns(2)
        
        with col1:
            if 'hashrate' in df.columns and df['hashrate'].notna().any():
                st.line_chart(df['hashrate'], height=200)
                st.caption("Hashrate (H/s) - Last 24h")
        
        with col2:
            if 'cpu_usage' in df.columns and df['cpu_usage'].notna().any():
                st.line_chart(df['cpu_usage'], height=200)
                st.caption("CPU Usage (%) - Last 24h")
                
    except Exception as e:
        st.error(f"Error loading history: {e}")


def display_database_info(db: SentinelDB):
    """Display database statistics in the sidebar."""
    try:
        stats = db.get_database_stats()
        
        st.sidebar.divider()
        st.sidebar.subheader("📊 Database Info")
        st.sidebar.metric("Total Miners", stats['total_miners'])
        st.sidebar.metric("Online Now", stats['online_miners'])
        st.sidebar.metric("History Records", stats['history_records'])
        st.sidebar.metric("P2Pool Miners", stats['p2pool_miners'])
        
        # Show alerts with warning if any exist
        alert_count = stats['unacknowledged_alerts']
        if alert_count > 0:
            st.sidebar.metric("🚨 Active Alerts", alert_count)
        else:
            st.sidebar.metric("Active Alerts", alert_count)
        
        # Cleanup button
        if st.sidebar.button("🗑️ Cleanup Old Data"):
            with st.spinner("Cleaning up..."):
                db.cleanup_old_data()
                st.sidebar.success("Cleanup complete!")
                st.rerun()
                
    except Exception as e:
        st.sidebar.error(f"Error loading stats: {e}")


def main():
    """Main function of the Sentinel Dashboard application."""
    
    # Title
    st.title("🛡️ Sentinel Dashboard")
    st.caption("Real-time monitoring for Monero miners and system health")
    
    # Get database connection
    db = get_database()
    
    # Sidebar configuration
    st.sidebar.title("⚙️ Settings")
    
    # View filter
    view_option = st.sidebar.radio(
        "View Filter",
        ["Online Only", "All Discovered Hosts"],
        help="Filter which miners to display"
    )
    
    # Auto-refresh toggle
    auto_refresh = st.sidebar.checkbox(
        "Auto Refresh",
        value=True,
        help=f"Automatically refresh every {config.DASHBOARD_REFRESH_INTERVAL}s"
    )
    
    # Manual refresh button
    if st.sidebar.button("🔄 Refresh Now"):
        import subprocess
        with st.spinner("Triggering probe for fresh data..."):
            try:
                # Trigger sentinel-probe.timer by starting its service explicitly
                subprocess.run(["systemctl", "start", "sentinel-probe.service"], capture_output=True, check=False)
            except Exception as e:
                st.sidebar.error(f"Failed to trigger probe: {e}")
        st.rerun()
    
    # Display database info
    display_database_info(db)
    
    # Main content area
    try:
        # Display Security Alerts first (most important)
        display_security_alerts(db)
        
        st.divider()
        
        # Display P2Pool stats
        display_p2pool_stats(db)
        
        st.divider()
        
        # Display miner stats
        display_miner_stats(db, view_option)
        
        # Footer with instructions
        with st.expander("ℹ️ How to use Sentinel"):
            st.markdown("""
            ### Getting Started
            
            1. **Monitor Local Miner:**
               ```bash
               python probe.py --host 127.0.0.1
               ```
            
            2. **Scan Network:**
               ```bash
               python probe.py --scan 192.168.1.0/24
               ```
            
            3. **Monitor P2Pool:**
               ```bash
               python probe.py --host 127.0.0.1 --p2pool-miner-address YOUR_ADDRESS
               ```
            
            4. **View Database Stats:**
               ```bash
               python probe.py --stats
               ```
            
            5. **Cleanup Old Data:**
               ```bash
               python probe.py --cleanup
               ```
            
            ### Automation
            Set up a cron job to run the probe periodically:
            ```bash
            # Run every 5 minutes
            */5 * * * * /path/to/python /path/to/probe.py --host 127.0.0.1
            ```
            """)
        
    except Exception as e:
        st.error(f"An error occurred: {e}")
        st.info("Try refreshing the page or checking the database connection.")
    
    # Auto-refresh logic
    if auto_refresh:
        import time
        time.sleep(config.DASHBOARD_REFRESH_INTERVAL)
        st.rerun()


if __name__ == "__main__":
    main()
    