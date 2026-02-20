#!/bin/bash
# Sentinel Setup Script for Linux
# Automated installation and configuration with guided prompts

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Banner
clear
echo -e "${CYAN}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     ███████╗███████╗███╗   ██╗████████╗██╗███╗   ██╗███████╗██╗     ║
║     ██╔════╝██╔════╝████╗  ██║╚══██╔══╝██║████╗  ██║██╔════╝██║     ║
║     ███████╗█████╗  ██╔██╗ ██║   ██║   ██║██╔██╗ ██║█████╗  ██║     ║
║     ╚════██║██╔══╝  ██║╚██╗██║   ██║   ██║██║╚██╗██║██╔══╝  ██║     ║
║     ███████║███████╗██║ ╚████║   ██║   ██║██║ ╚████║███████╗███████╗║
║     ╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝║
║                                                           ║
║         Monero Miner Monitoring & Security System         ║
║                    Automated Setup                        ║
╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo -e "${GREEN}Welcome to the Sentinel Setup Wizard!${NC}"
echo -e "This script will guide you through installing Sentinel on your system."
echo ""
sleep 2

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo -e "${RED}❌ Please do not run this script as root!${NC}"
    echo "Run as your normal user. We'll ask for sudo when needed."
    exit 1
fi

# Detect OS
echo -e "${BLUE}🔍 Detecting system...${NC}"
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
else
    OS=$(uname -s)
    VER=$(uname -r)
fi

echo -e "   OS: ${GREEN}$OS${NC}"
echo -e "   User: ${GREEN}$USER${NC}"
echo -e "   Home: ${GREEN}$HOME${NC}"
echo ""
sleep 1

# Get the original directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to prompt yes/no
prompt_yes_no() {
    while true; do
        read -p "$1 (y/n): " yn
        case $yn in
            [Yy]* ) return 0;;
            [Nn]* ) return 1;;
            * ) echo "Please answer yes or no.";;
        esac
    done
}

# Function to prompt with default value
prompt_with_default() {
    local prompt="$1"
    local default="$2"
    read -p "$prompt [$default]: " value
    echo "${value:-$default}"
}

# ============================================================================
# STEP 1: Installation Directory
# ============================================================================
echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}📁 Step 1: Installation Directory${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
echo ""

INSTALL_DIR=$(prompt_with_default "Where should Sentinel be installed?" "$HOME/sentinel")
echo ""

if [ "$INSTALL_DIR" = "$SCRIPT_DIR" ]; then
    echo -e "${GREEN}✓ Installing in current directory: $INSTALL_DIR${NC}"
elif [ -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}⚠️  Directory $INSTALL_DIR already exists!${NC}"
    if prompt_yes_no "Do you want to overwrite it?"; then
        echo "Backing up existing installation..."
        mv "$INSTALL_DIR" "$INSTALL_DIR.backup.$(date +%Y%m%d_%H%M%S)"
    else
        echo "Installation cancelled."
        exit 1
    fi
fi

mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

echo -e "${GREEN}✓ Installation directory: $INSTALL_DIR${NC}"
echo ""
sleep 1

# ============================================================================
# STEP 2: Install Dependencies
# ============================================================================
echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}📦 Step 2: System Dependencies${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
echo ""

echo "Sentinel requires:"
echo "  • Python 3.8+"
echo "  • pip (Python package manager)"
echo "  • SQLite3"
echo ""

if prompt_yes_no "Install system dependencies?"; then
    echo ""
    echo -e "${BLUE}Installing system packages...${NC}"
    
    if command -v apt-get &> /dev/null; then
        sudo apt-get update -qq
        sudo apt-get install -y python3 python3-pip python3-venv sqlite3
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y python3 python3-pip sqlite
    elif command -v yum &> /dev/null; then
        sudo yum install -y python3 python3-pip sqlite
    elif command -v pacman &> /dev/null; then
        sudo pacman -S --noconfirm python python-pip sqlite
    else
        echo -e "${YELLOW}⚠️  Could not detect package manager. Please install manually:${NC}"
        echo "   python3, pip, sqlite3"
        if ! prompt_yes_no "Continue anyway?"; then
            exit 1
        fi
    fi
    
    echo -e "${GREEN}✓ System dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠️  Skipping system dependencies. Make sure they're installed!${NC}"
fi
echo ""
sleep 1

# ============================================================================
# STEP 3: Download Sentinel Files
# ============================================================================
echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}⬇️  Step 3: Download Sentinel${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
echo ""

# Check if files exist in current directory
if [ -f "probe.py" ] && [ -f "app.py" ]; then
    echo -e "${GREEN}✓ Sentinel files found in current directory${NC}"
elif [ -f "$SCRIPT_DIR/probe.py" ] && [ -f "$SCRIPT_DIR/app.py" ]; then
    echo "Files found in script directory. Copying to installation folder..."
    cp -r "$SCRIPT_DIR/"* "$INSTALL_DIR/" 2>/dev/null || true
    echo -e "${GREEN}✓ Sentinel files copied to $INSTALL_DIR${NC}"
else
    echo "Sentinel files not found in current directory or script directory."
    echo "Options:"
    echo "  1. Extract from downloaded archive"
    echo "  2. Clone from GitHub (when released)"
    echo ""
    
    read -p "Enter path to Sentinel archive (.tar.gz or .zip): " ARCHIVE_PATH
    
    if [ -f "$ARCHIVE_PATH" ]; then
        echo "Extracting archive..."
        if [[ "$ARCHIVE_PATH" == *.tar.gz ]]; then
            tar -xzf "$ARCHIVE_PATH" -C "$INSTALL_DIR" --strip-components=1
        elif [[ "$ARCHIVE_PATH" == *.zip ]]; then
            unzip -q "$ARCHIVE_PATH" -d "$INSTALL_DIR"
        else
            echo -e "${RED}❌ Unsupported archive format${NC}"
            exit 1
        fi
        echo -e "${GREEN}✓ Files extracted${NC}"
    else
        echo -e "${RED}❌ Archive not found: $ARCHIVE_PATH${NC}"
        exit 1
    fi
fi
echo ""
sleep 1

# ============================================================================
# STEP 4: Python Virtual Environment
# ============================================================================
echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}🐍 Step 4: Python Environment${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
echo ""

if prompt_yes_no "Create Python virtual environment? (Recommended)"; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    
    echo "Installing Python packages..."
    pip install --upgrade pip -q
    pip install -r requirements.txt -q
    
    PYTHON_CMD="$INSTALL_DIR/venv/bin/python3"
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo "Installing Python packages globally..."
    pip3 install -r requirements.txt
    PYTHON_CMD=$(which python3)
    echo -e "${GREEN}✓ Python packages installed${NC}"
fi
echo ""
sleep 1

# ============================================================================
# STEP 5: Configuration
# ============================================================================
echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}⚙️  Step 5: Configuration${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
echo ""

# XMRig API Configuration
echo "XMRig API Configuration:"
echo "─────────────────────────"
MINER_PORT=$(prompt_with_default "XMRig API port" "18088")

echo ""
echo "To find your XMRig access token, run:"
echo "  cat ~/.xmrig/config.json | grep access-token"
echo "  or"
echo "  cat /etc/xmrig/config.json | grep access-token"
echo ""
read -p "XMRig API access token: " MINER_TOKEN

# P2Pool Configuration
echo ""
if prompt_yes_no "Do you use P2Pool?"; then
    echo ""
    echo "P2Pool Configuration:"
    echo "─────────────────────"
    read -p "Your Monero wallet address: " P2POOL_ADDRESS
    echo ""
    echo "P2Pool Network:"
    echo "  1. main (default, most hashrate)"
    echo "  2. mini (lower difficulty)"
    echo "  3. nano (lowest difficulty)"
    read -p "Select network [1-3]: " P2POOL_NETWORK_CHOICE
    
    case $P2POOL_NETWORK_CHOICE in
        1) P2POOL_NETWORK="main";;
        2) P2POOL_NETWORK="mini";;
        3) P2POOL_NETWORK="nano";;
        *) P2POOL_NETWORK="main";;
    esac
    
    USE_P2POOL=true
else
    USE_P2POOL=false
fi

# Update config.py
echo ""
echo "Writing configuration..."
cat > config.py << EOF
#!/usr/bin/env python3
"""
Configuration file for Sentinel monitoring system.
Generated by setup script on $(date)
"""

import os

# Database Configuration
DB_PATH = os.path.join(os.path.dirname(__file__), "sentinel.db")

# Miner API Configuration
DEFAULT_MINER_PORT = $MINER_PORT
MINER_API_TOKEN = "$MINER_TOKEN"
MINER_API_TIMEOUT = 2  # seconds

# P2Pool Configuration
P2POOL_NETWORKS = {
    "main": "https://p2pool.observer/",
    "mini": "https://mini.p2pool.observer/",
    "nano": "https://nano.p2pool.observer/",
}
P2POOL_API_TIMEOUT = 5  # seconds
P2POOL_WINDOW_SIZE = 2160

# Data Retention
DATA_RETENTION_DAYS = 30

# Dashboard Configuration
DASHBOARD_REFRESH_INTERVAL = 30  # seconds
DASHBOARD_PORT = 8501
EOF

echo -e "${GREEN}✓ Configuration saved${NC}"
echo ""
sleep 1

# ============================================================================
# STEP 6: Test Installation
# ============================================================================
echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}🧪 Step 6: Test Installation${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
echo ""

if prompt_yes_no "Run test scan now?"; then
    echo ""
    echo "Running test scan..."
    
    if [ "$USE_P2POOL" = true ]; then
        $PYTHON_CMD probe.py --host 127.0.0.1 --port $MINER_PORT \
            --p2pool-miner-address "$P2POOL_ADDRESS" \
            --p2pool-network "$P2POOL_NETWORK"
    else
        $PYTHON_CMD probe.py --host 127.0.0.1 --port $MINER_PORT
    fi
    
    echo ""
    echo "Checking database..."
    $PYTHON_CMD probe.py --stats
    
    echo ""
    echo -e "${GREEN}✓ Test scan complete${NC}"
fi
echo ""
sleep 1

# ============================================================================
# STEP 7: Systemd Services (Optional)
# ============================================================================
echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}🔧 Step 7: Systemd Services (Optional)${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
echo ""

echo "Systemd services enable automatic monitoring and dashboard startup."
echo ""

if prompt_yes_no "Set up systemd services?"; then
    echo ""
    
    # Probe Service
    echo "Creating sentinel-probe.service..."
    
    PROBE_EXEC="$PYTHON_CMD $INSTALL_DIR/probe.py --host 127.0.0.1 --port $MINER_PORT"
    if [ "$USE_P2POOL" = true ]; then
        PROBE_EXEC="$PROBE_EXEC --p2pool-miner-address $P2POOL_ADDRESS --p2pool-network $P2POOL_NETWORK"
    fi
    
    sudo tee /etc/systemd/system/sentinel-probe.service > /dev/null << EOF
[Unit]
Description=Sentinel Miner Monitoring Probe
After=network.target

[Service]
Type=oneshot
User=$USER
Group=$USER
WorkingDirectory=$INSTALL_DIR
ExecStart=$PROBE_EXEC

NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

    # Probe Timer
    echo "Creating sentinel-probe.timer..."
    sudo tee /etc/systemd/system/sentinel-probe.timer > /dev/null << EOF
[Unit]
Description=Run Sentinel Probe every 5 minutes
Requires=sentinel-probe.service

[Timer]
OnBootSec=1min
OnUnitActiveSec=5min
AccuracySec=1s

[Install]
WantedBy=timers.target
EOF

    # Dashboard Service
    if prompt_yes_no "Set up dashboard service?"; then
        echo "Creating sentinel-dash.service..."
        sudo tee /etc/systemd/system/sentinel-dash.service > /dev/null << EOF
[Unit]
Description=Sentinel Dashboard - Streamlit Interface
After=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$INSTALL_DIR
ExecStart=$PYTHON_CMD -m streamlit run $INSTALL_DIR/app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true --server.enableCORS false
Restart=always
RestartSec=10

NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF
        SETUP_DASH=true
    else
        SETUP_DASH=false
    fi
    
    # Enable services
    echo ""
    echo "Enabling services..."
    sudo systemctl daemon-reload
    sudo systemctl enable sentinel-probe.timer
    sudo systemctl start sentinel-probe.timer
    
    if [ "$SETUP_DASH" = true ]; then
        sudo systemctl enable sentinel-dash.service
        sudo systemctl start sentinel-dash.service
    fi
    
    echo -e "${GREEN}✓ Systemd services configured${NC}"
    SERVICES_ENABLED=true
else
    SERVICES_ENABLED=false
fi
echo ""
sleep 1

# ============================================================================
# STEP 8: Multi-Device Setup (Optional)
# ============================================================================
echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}🌐 Step 8: Multi-Device Setup (Optional)${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
echo ""

echo "If you have multiple mining devices, you can share the database via NFS."
echo ""

if prompt_yes_no "Set up database sharing?"; then
    echo ""
    echo "Database Sharing Options:"
    echo "  1. This is the main device (NFS server)"
    echo "  2. This is a secondary device (NFS client)"
    echo "  3. Skip for now"
    read -p "Select option [1-3]: " NFS_CHOICE
    
    case $NFS_CHOICE in
        1)
            echo ""
            if [ -f "./setup_nfs_server.sh" ]; then
                echo "Running NFS server setup..."
                sudo ./setup_nfs_server.sh
            else
                echo -e "${YELLOW}⚠️  setup_nfs_server.sh not found. Please run manually.${NC}"
            fi
            ;;
        2)
            echo ""
            read -p "Enter the IP address of the main device: " SERVER_IP
            if [ -f "./setup_nfs_client.sh" ]; then
                echo "Running NFS client setup..."
                sudo ./setup_nfs_client.sh "$SERVER_IP"
            else
                echo -e "${YELLOW}⚠️  setup_nfs_client.sh not found. Please run manually.${NC}"
            fi
            ;;
        3)
            echo "Skipping database sharing setup."
            ;;
    esac
fi
echo ""

# ============================================================================
# INSTALLATION COMPLETE
# ============================================================================
clear
echo -e "${GREEN}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║                  ✓ Installation Complete!                ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo -e "${CYAN}Installation Summary:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "📁 Install Location:   ${GREEN}$INSTALL_DIR${NC}"
echo -e "🐍 Python:             ${GREEN}$PYTHON_CMD${NC}"
echo -e "⚙️  Config File:        ${GREEN}$INSTALL_DIR/config.py${NC}"
echo -e "💾 Database:           ${GREEN}$INSTALL_DIR/sentinel.db${NC}"

if [ "$SERVICES_ENABLED" = true ]; then
    echo -e "🔧 Systemd Services:   ${GREEN}Enabled${NC}"
else
    echo -e "🔧 Systemd Services:   ${YELLOW}Not configured${NC}"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo -e "${CYAN}Quick Start Guide:${NC}"
echo ""

if [ "$SERVICES_ENABLED" = true ]; then
    echo "✓ Services are running automatically!"
    echo ""
    echo "Check service status:"
    echo "  sudo systemctl status sentinel-probe.timer"
    if [ "$SETUP_DASH" = true ]; then
        echo "  sudo systemctl status sentinel-dash.service"
    fi
    echo ""
    echo "View logs:"
    echo "  journalctl -u sentinel-probe.service -f"
    if [ "$SETUP_DASH" = true ]; then
        echo "  journalctl -u sentinel-dash.service -f"
    fi
else
    echo "Manual operation:"
    echo ""
    echo "1. Run probe manually:"
    if [ "$USE_P2POOL" = true ]; then
        echo "   $PYTHON_CMD $INSTALL_DIR/probe.py --host 127.0.0.1 \\"
        echo "     --port $MINER_PORT \\"
        echo "     --p2pool-miner-address $P2POOL_ADDRESS \\"
        echo "     --p2pool-network $P2POOL_NETWORK"
    else
        echo "   $PYTHON_CMD $INSTALL_DIR/probe.py --host 127.0.0.1 --port $MINER_PORT"
    fi
    echo ""
    echo "2. Start dashboard:"
    echo "   $PYTHON_CMD -m streamlit run $INSTALL_DIR/app.py"
fi

echo ""
echo "Access Dashboard:"
if [ "$SETUP_DASH" = true ]; then
    echo "  http://localhost:8501"
    echo "  http://$(hostname -I | awk '{print $1}'):8501"
else
    echo "  Run: streamlit run $INSTALL_DIR/app.py"
    echo "  Then visit: http://localhost:8501"
fi

echo ""
echo "View database stats:"
echo "  $PYTHON_CMD $INSTALL_DIR/probe.py --stats"

echo ""
echo "Useful commands:"
echo "  cd $INSTALL_DIR"
echo "  $PYTHON_CMD probe.py --help"
echo "  $PYTHON_CMD diagnose_p2pool.py YOUR_ADDRESS --network $P2POOL_NETWORK"

echo ""
echo -e "${YELLOW}📖 Documentation:${NC}"
echo "  • README.md - Complete guide"
echo "  • SYSTEMD_SETUP.md - Service management"
echo "  • HOSTNAME_MANAGEMENT.md - Multi-device setup"
echo "  • P2POOL_TROUBLESHOOTING.md - P2Pool help"

echo ""
echo -e "${GREEN}🎉 Happy Mining!${NC}"
echo -e "${CYAN}If you find Sentinel useful, consider starring us on GitHub!${NC}"
echo ""
