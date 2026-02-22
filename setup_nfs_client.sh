#!/bin/bash
# Sentinel NFS Client Setup Script
# Run this on secondary devices to connect to the shared database

set -e  # Exit on error

echo "=========================================="
echo "  Sentinel NFS Client Setup"
echo "  This device will connect to shared database"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ This script must be run as root (use sudo)"
    exit 1
fi

# Get the actual user (not root if using sudo)
ACTUAL_USER="${SUDO_USER:-$USER}"
ACTUAL_HOME=$(eval echo ~$ACTUAL_USER)

# Get server IP from command line argument
if [ -z "$1" ]; then
    echo "❌ Error: NFS server IP address required"
    echo ""
    echo "Usage: sudo ./setup_nfs_client.sh SERVER_IP"
    echo "Example: sudo ./setup_nfs_client.sh 192.168.1.100"
    exit 1
fi

SERVER_IP="$1"

# Configuration
SHARED_DIR="/opt/sentinel-shared"
SENTINEL_DIR="$ACTUAL_HOME/sentinel"

echo "📋 Configuration:"
echo "   User: $ACTUAL_USER"
echo "   NFS Server: $SERVER_IP"
echo "   Sentinel directory: $SENTINEL_DIR"
echo "   Mount point: $SHARED_DIR"
echo ""

read -p "Does this look correct? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cancelled."
    exit 1
fi

# Step 1: Install NFS client
echo ""
echo "📦 Step 1: Installing NFS client..."
apt-get update -qq
apt-get install -y nfs-common

# Step 2: Create mount point
echo ""
echo "📁 Step 2: Creating mount point..."
mkdir -p "$SHARED_DIR"

# Step 3: Test NFS connection
echo ""
echo "🔍 Step 3: Testing NFS server connection..."
if showmount -e "$SERVER_IP" | grep -q "$SHARED_DIR"; then
    echo "   ✅ NFS server is accessible"
else
    echo "   ❌ Cannot connect to NFS server at $SERVER_IP"
    echo "   Please check:"
    echo "   - Server IP is correct"
    echo "   - NFS server is running: sudo systemctl status nfs-kernel-server"
    echo "   - Firewall allows NFS traffic"
    exit 1
fi

# Step 4: Mount the NFS share
echo ""
echo "💾 Step 4: Mounting NFS share..."
if mountpoint -q "$SHARED_DIR"; then
    echo "   ⚠️  Already mounted, unmounting first..."
    umount "$SHARED_DIR"
fi

mount -t nfs "$SERVER_IP:$SHARED_DIR" "$SHARED_DIR"
echo "   ✅ Mounted successfully"

# Step 5: Add to /etc/fstab for automatic mounting
echo ""
echo "📝 Step 5: Configuring automatic mount..."
FSTAB_LINE="$SERVER_IP:$SHARED_DIR $SHARED_DIR nfs defaults,_netdev 0 0"

if grep -q "$SERVER_IP:$SHARED_DIR" /etc/fstab; then
    echo "   ⚠️  Entry already in /etc/fstab, skipping..."
else
    echo "$FSTAB_LINE" >> /etc/fstab
    echo "   ✅ Added to /etc/fstab"
fi

# Step 6: Remove local database if it exists
echo ""
echo "🗑️  Step 6: Removing local database..."
if [ -f "$SENTINEL_DIR/sentinel.db" ]; then
    echo "   Creating backup of local database..."
    mv "$SENTINEL_DIR/sentinel.db" "$SENTINEL_DIR/sentinel.db.local_backup"
    [ -f "$SENTINEL_DIR/sentinel.db-wal" ] && mv "$SENTINEL_DIR/sentinel.db-wal" "$SENTINEL_DIR/sentinel.db-wal.local_backup"
    [ -f "$SENTINEL_DIR/sentinel.db-shm" ] && mv "$SENTINEL_DIR/sentinel.db-shm" "$SENTINEL_DIR/sentinel.db-shm.local_backup"
    echo "   ✅ Local database backed up"
else
    echo "   ℹ️  No local database found"
fi

# Step 7: Update config.py
echo ""
echo "⚙️  Step 7: Updating config.py..."
if [ -f "$SENTINEL_DIR/config.py" ]; then
    # Backup original
    cp "$SENTINEL_DIR/config.py" "$SENTINEL_DIR/config.py.backup"
    
    # Update DB_PATH
    sed -i "s|^DB_PATH = .*|DB_PATH = \"$SHARED_DIR/sentinel.db\"|" "$SENTINEL_DIR/config.py"
    
    echo "   ✅ Updated DB_PATH in config.py"
    echo "   ℹ️  Backup saved to config.py.backup"
else
    echo "   ⚠️  config.py not found - please update manually"
fi

# Step 8: Stagger the probe timer
echo ""
echo "⏰ Step 8: Staggering probe timer..."
TIMER_FILE="/etc/systemd/system/sentinel-probe.timer"

if [ -f "$TIMER_FILE" ]; then
    # Change OnBootSec to 3min (stagger from server's 1min)
    sed -i 's/OnBootSec=1min/OnBootSec=3min/' "$TIMER_FILE"
    systemctl daemon-reload
    echo "   ✅ Timer staggered to avoid conflicts"
else
    echo "   ⚠️  Timer file not found - please configure manually"
fi

# Step 9: Restart Sentinel services
echo ""
echo "🔄 Step 9: Restarting Sentinel services..."
if systemctl is-active --quiet sentinel-probe.timer; then
    systemctl restart sentinel-probe.timer
    echo "   ✅ Restarted sentinel-probe.timer"
fi

if systemctl is-active --quiet sentinel-dash.service; then
    systemctl restart sentinel-dash.service
    echo "   ✅ Restarted sentinel-dash.service"
fi

echo ""
echo "=========================================="
echo "✅ NFS Client Setup Complete!"
echo "=========================================="
echo ""
echo "📋 Summary:"
echo ""
echo "✅ Connected to NFS server at $SERVER_IP"
echo "✅ Shared database mounted at $SHARED_DIR"
echo "✅ Config updated to use shared database"
echo "✅ Timer staggered to avoid conflicts"
echo ""
echo "🧪 Test the setup:"
echo ""
echo "1. Check if database is accessible:"
echo "   ls -lh $SHARED_DIR/sentinel.db"
echo ""
echo "2. Run a probe:"
echo "   python3 $SENTINEL_DIR/probe.py --host 127.0.0.1"
echo ""
echo "3. Check database stats:"
echo "   python3 $SENTINEL_DIR/probe.py --stats"
echo ""
echo "4. Open dashboard (should show data from both devices):"
echo "   http://localhost:8501"
echo ""
echo "=========================================="
