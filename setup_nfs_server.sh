#!/bin/bash
# Sentinel NFS Server Setup Script
# Run this on the MAIN device that will host the shared database

set -e  # Exit on error

echo "=========================================="
echo "  Sentinel NFS Server Setup"
echo "  This device will host the shared database"
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

# Configuration
SHARED_DIR="/opt/sentinel-shared"
SENTINEL_DIR="$ACTUAL_HOME/sentinel"
NETWORK_RANGE="192.168.1.0/24"  # Change this to match your network

echo "📋 Configuration:"
echo "   User: $ACTUAL_USER"
echo "   Sentinel directory: $SENTINEL_DIR"
echo "   Shared directory: $SHARED_DIR"
echo "   Network range: $NETWORK_RANGE"
echo ""

read -p "Does this look correct? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cancelled. Please edit this script to set correct values."
    exit 1
fi

# Step 1: Install NFS server
echo ""
echo "📦 Step 1: Installing NFS server..."
apt-get update -qq || true
apt-get install -y nfs-kernel-server

# Step 2: Create shared directory
echo ""
echo "📁 Step 2: Creating shared directory..."
mkdir -p "$SHARED_DIR"
chown "$ACTUAL_USER:$ACTUAL_USER" "$SHARED_DIR"
chmod 755 "$SHARED_DIR"

# Step 3: Move database to shared location
echo ""
echo "💾 Step 3: Moving database to shared directory..."
if [ -f "$SENTINEL_DIR/sentinel.db" ]; then
    echo "   Moving $SENTINEL_DIR/sentinel.db to $SHARED_DIR/"
    mv "$SENTINEL_DIR/sentinel.db" "$SHARED_DIR/"
    
    # Also move WAL files if they exist
    [ -f "$SENTINEL_DIR/sentinel.db-wal" ] && mv "$SENTINEL_DIR/sentinel.db-wal" "$SHARED_DIR/"
    [ -f "$SENTINEL_DIR/sentinel.db-shm" ] && mv "$SENTINEL_DIR/sentinel.db-shm" "$SHARED_DIR/"
    
    echo "   ✅ Database moved"
else
    echo "   ℹ️  No existing database found - will be created on first run"
fi

# Step 4: Configure NFS exports
echo ""
echo "🌐 Step 4: Configuring NFS exports..."
EXPORT_LINE="$SHARED_DIR $NETWORK_RANGE(rw,sync,no_subtree_check,no_root_squash)"

if grep -q "$SHARED_DIR" /etc/exports; then
    echo "   ⚠️  Export already exists, skipping..."
else
    echo "$EXPORT_LINE" >> /etc/exports
    echo "   ✅ Added export to /etc/exports"
fi

# Step 5: Apply NFS configuration
echo ""
echo "🔄 Step 5: Applying NFS configuration..."
exportfs -ra
systemctl restart nfs-kernel-server
systemctl enable nfs-kernel-server

# Step 6: Update config.py
echo ""
echo "⚙️  Step 6: Updating config.py..."
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

# Step 7: Show firewall note
echo ""
echo "🔥 Step 7: Firewall configuration (if applicable)..."
echo "   If you have a firewall enabled, you may need to allow NFS:"
echo "   sudo ufw allow from $NETWORK_RANGE to any port nfs"

# Step 8: Restart Sentinel services
echo ""
echo "🔄 Step 8: Restarting Sentinel services..."
if systemctl is-active --quiet sentinel-probe.timer; then
    systemctl restart sentinel-probe.timer
    echo "   ✅ Restarted sentinel-probe.timer"
fi

if systemctl is-active --quiet sentinel-dash.service; then
    systemctl restart sentinel-dash.service
    echo "   ✅ Restarted sentinel-dash.service"
fi

# Get server IP
SERVER_IP=$(hostname -I | awk '{print $1}')

echo ""
echo "=========================================="
echo "✅ NFS Server Setup Complete!"
echo "=========================================="
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Note your server IP address: $SERVER_IP"
echo ""
echo "2. On other devices, run:"
echo "   sudo ./setup_nfs_client.sh $SERVER_IP"
echo ""
echo "3. All devices will now share the database at:"
echo "   $SHARED_DIR/sentinel.db"
echo ""
echo "4. Test by running probe on this device:"
echo "   python3 $SENTINEL_DIR/probe.py --host 127.0.0.1"
echo ""
echo "5. Check the database:"
echo "   python3 $SENTINEL_DIR/probe.py --stats"
echo ""
echo "=========================================="
