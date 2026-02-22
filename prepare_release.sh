#!/bin/bash
# Release Preparation Script for Sentinel
# Creates distribution archives for Linux and Windows

set -e

VERSION="1.0.1"
RELEASE_DIR="release"
PROJECT_NAME="sentinel"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║        Sentinel Release Package Generator                ║"
echo "║                  Version $VERSION                         ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Clean previous release
if [ -d "$RELEASE_DIR" ]; then
    echo -e "${YELLOW}Cleaning previous release...${NC}"
    rm -rf "$RELEASE_DIR"
fi

mkdir -p "$RELEASE_DIR"

# ============================================================================
# Linux Release
# ============================================================================
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Creating Linux Release Package${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"

LINUX_DIR="$RELEASE_DIR/${PROJECT_NAME}-linux-v${VERSION}"
mkdir -p "$LINUX_DIR"

echo "Copying files..."

# Core Python files
cp *.py "$LINUX_DIR/" 2>/dev/null || true

# Configuration and data files
cp requirements.txt "$LINUX_DIR/"
cp .gitignore "$LINUX_DIR/"

# Documentation
cp *.md "$LINUX_DIR/"

# Setup scripts
cp setup_linux.sh "$LINUX_DIR/"
cp setup_nfs_server.sh "$LINUX_DIR/"
cp setup_nfs_client.sh "$LINUX_DIR/"
chmod +x "$LINUX_DIR"/*.sh

# Systemd files
cp *.service "$LINUX_DIR/" 2>/dev/null || true
cp *.timer "$LINUX_DIR/" 2>/dev/null || true

# Create Linux-specific README
cat > "$LINUX_DIR/README_LINUX.md" << 'EOF'
# Sentinel for Linux - Quick Start

## Automated Setup (Recommended)

```bash
chmod +x setup_linux.sh
./setup_linux.sh
```

The setup wizard will guide you through:
- Installing dependencies
- Configuring XMRig API
- Setting up P2Pool monitoring
- Creating systemd services
- Database configuration

## Manual Installation

1. **Install Dependencies:**
   ```bash
   sudo apt-get install python3 python3-pip sqlite3
   pip3 install -r requirements.txt
   ```

2. **Configure:**
   ```bash
   nano config.py  # Edit your API token and settings
   ```

3. **Run Probe:**
   ```bash
   python3 probe.py --host 127.0.0.1 --port 18088
   ```

4. **Start Dashboard:**
   ```bash
   streamlit run app.py
   ```
   Visit: http://localhost:8501

## Systemd Services

For automatic startup:

```bash
# Install services
sudo cp sentinel-probe.service /etc/systemd/system/
sudo cp sentinel-probe.timer /etc/systemd/system/
sudo cp sentinel-dash.service /etc/systemd/system/

# Edit service files with your paths
sudo nano /etc/systemd/system/sentinel-probe.service

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable sentinel-probe.timer
sudo systemctl start sentinel-probe.timer
sudo systemctl enable sentinel-dash.service
sudo systemctl start sentinel-dash.service
```

## Multi-Device Setup

Share database across multiple miners:

```bash
# On main device
sudo ./setup_nfs_server.sh

# On secondary devices
sudo ./setup_nfs_client.sh MAIN_DEVICE_IP
```

## Documentation

- `README.md` - Complete guide
- `SYSTEMD_SETUP.md` - Service management
- `HOSTNAME_MANAGEMENT.md` - Multi-device configuration
- `DATABASE_SHARING.md` - NFS setup guide
- `P2POOL_TROUBLESHOOTING.md` - P2Pool help

## Support

GitHub: https://github.com/yourusername/sentinel
Issues: https://github.com/yourusername/sentinel/issues
EOF

echo "Creating Linux archive..."
cd "$RELEASE_DIR"
tar -czf "${PROJECT_NAME}-linux-v${VERSION}.tar.gz" "${PROJECT_NAME}-linux-v${VERSION}"
cd ..

echo -e "${GREEN}✓ Linux package created: ${PROJECT_NAME}-linux-v${VERSION}.tar.gz${NC}"

# ============================================================================
# Windows Release
# ============================================================================
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Creating Windows Release Package${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"

WINDOWS_DIR="$RELEASE_DIR/${PROJECT_NAME}-windows-v${VERSION}"
mkdir -p "$WINDOWS_DIR"

echo "Copying files..."

# Core Python files
cp *.py "$WINDOWS_DIR/" 2>/dev/null || true

# Configuration and data files
cp requirements.txt "$WINDOWS_DIR/"
cp .gitignore "$WINDOWS_DIR/"

# Documentation
cp *.md "$WINDOWS_DIR/"

# Windows setup script
cp setup_windows.ps1 "$WINDOWS_DIR/"

# Create batch launcher
cat > "$WINDOWS_DIR/SentinelSetup.bat" << 'EOF'
@echo off
title Sentinel Setup
echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║                  Sentinel Setup                           ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

REM Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo.
    echo Please install Python 3.8 or later from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation!
    echo.
    pause
    exit /b 1
)

echo Python found. Starting setup wizard...
echo.

REM Run PowerShell setup
powershell -ExecutionPolicy Bypass -File "%~dp0setup_windows.ps1"

if errorlevel 1 (
    echo.
    echo [ERROR] Setup failed. Please check the error messages above.
    echo.
    pause
    exit /b 1
)

echo.
echo Setup complete!
pause
EOF

# Create Windows-specific README
cat > "$WINDOWS_DIR/README_WINDOWS.md" << 'EOF'
# Sentinel for Windows - Quick Start

## Automated Setup (Recommended)

1. **Extract the ZIP file**
2. **Double-click `SentinelSetup.bat`**
3. **Follow the setup wizard**

The wizard will:
- Check for Python
- Install dependencies
- Configure your miner settings
- Create desktop shortcuts
- Set up scheduled tasks (optional)

## Requirements

- Windows 10 or later (Windows 11 supported)
- Python 3.8 or later
  - Download from: https://www.python.org/downloads/
  - **Important:** Check "Add Python to PATH" during installation!

## Manual Setup

If the automated setup doesn't work:

1. **Install Python** (if not already installed)

2. **Open PowerShell as Administrator:**
   - Right-click Start button
   - Select "Windows PowerShell (Admin)"

3. **Navigate to Sentinel folder:**
   ```powershell
   cd C:\path\to\sentinel
   ```

4. **Allow script execution:**
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

5. **Run setup:**
   ```powershell
   .\setup_windows.ps1
   ```

## After Installation

### Start Dashboard

- Double-click the "Sentinel Dashboard" desktop shortcut
- OR visit http://localhost:8501 in your browser

### Run Probe Manually

- Double-click the "Sentinel Probe" desktop shortcut
- OR open PowerShell and run:
  ```powershell
  cd C:\Users\YourName\sentinel
  python probe.py --host 127.0.0.1 --port 18088
  ```

### View Statistics

```powershell
cd C:\Users\YourName\sentinel
python probe.py --stats
```

## Scheduled Tasks

If you set up scheduled tasks during installation:

1. Press `Win + R`
2. Type `taskschd.msc`
3. Look for "SentinelProbe" task
4. You can enable/disable or modify the schedule

## Troubleshooting

### Python Not Found

- Install from https://www.python.org/downloads/
- During installation, check "Add Python to PATH"
- Restart your computer after installation

### PowerShell Execution Error

```powershell
# Run as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### XMRig Connection Failed

1. Check XMRig is running
2. Verify XMRig API port (usually 18088)
3. Check XMRig access token in `config.json`
4. Update Sentinel's `config.py` with correct token

### Dashboard Won't Start

- Check if port 8501 is available
- Try: `netstat -ano | findstr :8501`
- If in use, stop that process or change the port in `config.py`

## Firewall

If accessing dashboard from another computer:

1. Open Windows Firewall
2. Allow inbound connections on port 8501
3. Access via: http://YOUR_PC_IP:8501

## Documentation

- `README.md` - Complete documentation
- `P2POOL_TROUBLESHOOTING.md` - P2Pool setup help
- `BUILDING_WINDOWS_EXE.md` - For developers

## Support

- GitHub Issues: https://github.com/yourusername/sentinel/issues
- Monero Mining Subreddit: r/MoneroMining

## Uninstall

1. Delete the Sentinel folder
2. Remove scheduled tasks (if created):
   - Open Task Scheduler
   - Delete "SentinelProbe" task
3. Remove desktop shortcuts
EOF

echo "Creating Windows archive..."
cd "$RELEASE_DIR"
python3 -m zipfile -c "${PROJECT_NAME}-windows-v${VERSION}.zip" "${PROJECT_NAME}-windows-v${VERSION}"
cd ..

echo -e "${GREEN}✓ Windows package created: ${PROJECT_NAME}-windows-v${VERSION}.zip${NC}"

# ============================================================================
# Create Checksums
# ============================================================================
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Generating Checksums${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"

cd "$RELEASE_DIR"

# SHA256 checksums
sha256sum "${PROJECT_NAME}-linux-v${VERSION}.tar.gz" > "${PROJECT_NAME}-v${VERSION}-checksums.txt"
sha256sum "${PROJECT_NAME}-windows-v${VERSION}.zip" >> "${PROJECT_NAME}-v${VERSION}-checksums.txt"

echo ""
echo "Checksums:"
cat "${PROJECT_NAME}-v${VERSION}-checksums.txt"

cd ..

echo ""
echo -e "${GREEN}✓ Checksums generated${NC}"

# ============================================================================
# Create Release Notes
# ============================================================================
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Generating Release Notes${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"

cat > "$RELEASE_DIR/RELEASE_NOTES.md" << EOF
# Sentinel v${VERSION} Release Notes

## 🎉 What's New in v1.0.1

This patch release addresses a bug in the automated Linux setup script.

### 🐛 Bug Fixes

- **Linux Setup**: Fixed an issue where the installation script would rename the entire script directory, breaking the installation flow when the repository files were adjacent.

### Features

- **Real-time Monitoring**: Track hashrate, CPU, and RAM usage across multiple devices
- **P2Pool Integration**: Monitor your P2Pool shares, payouts, and statistics
- **Network Security**: Built-in NIDS (Network Intrusion Detection System) with ARP spoofing detection
- **Multi-Device Support**: Share database across devices using NFS
- **Beautiful Dashboard**: Real-time Streamlit web interface
- **Automatic Hostname Detection**: No more conflicts when monitoring multiple devices
- **Historical Data**: Track performance over time with charts
- **Systemd/Task Scheduler Integration**: Automatic monitoring
- **SQLite Storage**: Fast, local, no cloud dependencies

### Supported Platforms

- **Linux**: Ubuntu, Debian, Fedora, Arch, and more
- **Windows**: Windows 10, Windows 11

### Installation

#### Linux
\`\`\`bash
tar -xzf sentinel-linux-v${VERSION}.tar.gz
cd sentinel-linux-v${VERSION}
chmod +x setup_linux.sh
./setup_linux.sh
\`\`\`

#### Windows
1. Extract \`sentinel-windows-v${VERSION}.zip\`
2. Double-click \`SentinelSetup.bat\`
3. Follow the wizard

### Requirements

- Python 3.8+
- XMRig with HTTP API enabled
- (Optional) P2Pool node for P2Pool monitoring
- (Optional) Root access for NIDS functionality

### Documentation

- \`README.md\` - Complete guide
- \`SYSTEMD_SETUP.md\` - Systemd service setup (Linux)
- \`HOSTNAME_MANAGEMENT.md\` - Multi-device configuration
- \`DATABASE_SHARING.md\` - Database sharing via NFS
- \`P2POOL_TROUBLESHOOTING.md\` - P2Pool troubleshooting
- \`README_LINUX.md\` / \`README_WINDOWS.md\` - Platform-specific guides

### Checksums

\`\`\`
$(cat "$RELEASE_DIR/${PROJECT_NAME}-v${VERSION}-checksums.txt")
\`\`\`

## 🐛 Known Issues

None at this time.

## 🙏 Acknowledgments

Special thanks to the Monero Mining community on Reddit for feedback and testing!

## 📞 Support

- **GitHub Issues**: https://github.com/yourusername/sentinel/issues
- **Discussions**: https://github.com/yourusername/sentinel/discussions
- **Reddit**: r/MoneroMining

## 📄 License

MIT License - See LICENSE file for details

---

**Happy Mining! ⛏️**
EOF

echo -e "${GREEN}✓ Release notes generated${NC}"

# ============================================================================
# Summary
# ============================================================================
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Release Package Summary${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""

echo "Release files created in: $RELEASE_DIR/"
echo ""
echo "Archives:"
ls -lh "$RELEASE_DIR"/*.tar.gz "$RELEASE_DIR"/*.zip 2>/dev/null
echo ""
echo "Checksums:"
cat "$RELEASE_DIR/${PROJECT_NAME}-v${VERSION}-checksums.txt"
echo ""

echo -e "${GREEN}✓ Release preparation complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Test the archives on clean systems"
echo "2. Create a GitHub release"
echo "3. Upload the archives and checksums"
echo "4. Copy RELEASE_NOTES.md to GitHub release description"
echo ""
echo "GitHub Release Command:"
echo "  gh release create v${VERSION} \\"
echo "    $RELEASE_DIR/${PROJECT_NAME}-linux-v${VERSION}.tar.gz \\"
echo "    $RELEASE_DIR/${PROJECT_NAME}-windows-v${VERSION}.zip \\"
echo "    $RELEASE_DIR/${PROJECT_NAME}-v${VERSION}-checksums.txt \\"
echo "    --title \"Sentinel v${VERSION}\" \\"
echo "    --notes-file $RELEASE_DIR/RELEASE_NOTES.md"
echo ""
