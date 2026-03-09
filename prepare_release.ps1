<#
.SYNOPSIS
    Release Preparation Script for Sentinel (Windows/PowerShell version)
.DESCRIPTION
    Creates distribution archives for Linux and Windows
#>

$ErrorActionPreference = "Stop"

$VERSION = "1.0.3"
$RELEASE_DIR = "release"
$PROJECT_NAME = "sentinel"

# Colors mapping for Write-Host
$colorGreen = "Green"
$colorBlue = "Cyan"
$colorYellow = "Yellow"

Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor $colorBlue
Write-Host "║        Sentinel Release Package Generator                ║" -ForegroundColor $colorBlue
Write-Host "║                  Version $VERSION                         ║" -ForegroundColor $colorBlue
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor $colorBlue
Write-Host ""

# Clean previous release
if (Test-Path $RELEASE_DIR) {
    Write-Host "Cleaning previous release..." -ForegroundColor $colorYellow
    Remove-Item -Recurse -Force $RELEASE_DIR
}

New-Item -ItemType Directory -Force -Path $RELEASE_DIR | Out-Null

# ============================================================================
# Linux Release
# ============================================================================
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor $colorBlue
Write-Host "Creating Linux Release Package" -ForegroundColor $colorGreen
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor $colorBlue

$LINUX_DIR_NAME = "$PROJECT_NAME-linux-v$VERSION"
$LINUX_DIR = Join-Path $RELEASE_DIR $LINUX_DIR_NAME
New-Item -ItemType Directory -Force -Path $LINUX_DIR | Out-Null

Write-Host "Copying files..."

# Core Python files
Copy-Item *.py -Destination $LINUX_DIR -ErrorAction SilentlyContinue

# Configuration and data files
Copy-Item requirements.txt -Destination $LINUX_DIR
Copy-Item .gitignore -Destination $LINUX_DIR

# Documentation
Copy-Item *.md -Destination $LINUX_DIR

# Setup scripts
Copy-Item *.sh -Destination $LINUX_DIR -ErrorAction SilentlyContinue

# Systemd files
Copy-Item *.service -Destination $LINUX_DIR -ErrorAction SilentlyContinue
Copy-Item *.timer -Destination $LINUX_DIR -ErrorAction SilentlyContinue

# Create Linux-specific README
$readmeLinuxContent = @"
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
"@
Set-Content -Path (Join-Path $LINUX_DIR "README_LINUX.md") -Value $readmeLinuxContent -Encoding utf8

Write-Host "Creating Linux archive..."
Push-Location $RELEASE_DIR
# Using built-in tar (available in Windows 10/11)
Invoke-Expression "tar -czf `"$LINUX_DIR_NAME.tar.gz`" `"$LINUX_DIR_NAME`""
Pop-Location

Write-Host "✓ Linux package created: $LINUX_DIR_NAME.tar.gz" -ForegroundColor $colorGreen

# ============================================================================
# Windows Release
# ============================================================================
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor $colorBlue
Write-Host "Creating Windows Release Package" -ForegroundColor $colorGreen
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor $colorBlue

$WINDOWS_DIR_NAME = "$PROJECT_NAME-windows-v$VERSION"
$WINDOWS_DIR = Join-Path $RELEASE_DIR $WINDOWS_DIR_NAME
New-Item -ItemType Directory -Force -Path $WINDOWS_DIR | Out-Null

Write-Host "Copying files..."

# Core Python files
Copy-Item *.py -Destination $WINDOWS_DIR -ErrorAction SilentlyContinue

# Configuration and data files
Copy-Item requirements.txt -Destination $WINDOWS_DIR
Copy-Item .gitignore -Destination $WINDOWS_DIR

# Documentation
Copy-Item *.md -Destination $WINDOWS_DIR

# Windows setup script
Copy-Item setup_windows.ps1 -Destination $WINDOWS_DIR

# Create batch launcher
$sentinelSetupContent = @"
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
"@
Set-Content -Path (Join-Path $WINDOWS_DIR "SentinelSetup.bat") -Value $sentinelSetupContent -Encoding utf8

# Create Windows-specific README
$readmeWindowsContent = @"
# Sentinel for Windows - Quick Start

## Automated Setup (Recommended)

1. **Extract the ZIP file**
2. **Double-click `SentinelSetup.bat`**
3. **Follow the setup wizard**

The wizard will:
- Check for Python
- Configure your miner settings
- Download and install NSSM (Non-Sucking Service Manager)
- Setup background services to run the Probe and Dashboard automatically
- Configure Windows Firewall for tailscale/LAN access
- Create desktop shortcuts

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

## Background Services

If you installed the background services during setup, Sentinel runs silently in the background via NSSM.

To restart or check the status of these services, open an **Administrator PowerShell** and run:

```powershell
# Restart the dashboard
Restart-Service sentinel-dash -Force

# Restart the probe
Restart-Service sentinel-probe -Force

# Check service status via NSSM
& "`$env:LOCALAPPDATA\Microsoft\WinGet\Links\nssm.exe" status sentinel-dash
& "`$env:LOCALAPPDATA\Microsoft\WinGet\Links\nssm.exe" status sentinel-probe
```

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

1. Remove the background services (Open PowerShell as Administrator):
   ```powershell
   Stop-Service sentinel-dash -Force
   Stop-Service sentinel-probe -Force
   & "`$env:LOCALAPPDATA\Microsoft\WinGet\Links\nssm.exe" remove sentinel-dash confirm
   & "`$env:LOCALAPPDATA\Microsoft\WinGet\Links\nssm.exe" remove sentinel-probe confirm
   ```
2. Delete the Sentinel folder
3. Remove desktop shortcuts
"@
Set-Content -Path (Join-Path $WINDOWS_DIR "README_WINDOWS.md") -Value $readmeWindowsContent -Encoding utf8

Write-Host "Creating Windows archive..."
Push-Location $RELEASE_DIR
Compress-Archive -Path $WINDOWS_DIR_NAME -DestinationPath "$WINDOWS_DIR_NAME.zip" -Force
Pop-Location

Write-Host "✓ Windows package created: $WINDOWS_DIR_NAME.zip" -ForegroundColor $colorGreen

# ============================================================================
# Create Checksums
# ============================================================================
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor $colorBlue
Write-Host "Generating Checksums" -ForegroundColor $colorGreen
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor $colorBlue

Push-Location $RELEASE_DIR

$linuxArchive = "$PROJECT_NAME-linux-v$VERSION.tar.gz"
$windowsArchive = "$PROJECT_NAME-windows-v$VERSION.zip"
$checksumFile = "$PROJECT_NAME-v$VERSION-checksums.txt"

$linuxHash = (Get-FileHash -Algorithm SHA256 -Path $linuxArchive).Hash.ToLower()
$windowsHash = (Get-FileHash -Algorithm SHA256 -Path $windowsArchive).Hash.ToLower()

"$linuxHash  $linuxArchive" | Out-File -FilePath $checksumFile -Encoding ASCII
"$windowsHash  $windowsArchive" | Out-File -FilePath $checksumFile -Encoding ASCII -Append

Write-Host ""
Write-Host "Checksums:"
Get-Content $checksumFile

Pop-Location

Write-Host ""
Write-Host "✓ Checksums generated" -ForegroundColor $colorGreen

# ============================================================================
# Create Release Notes
# ============================================================================
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor $colorBlue
Write-Host "Generating Release Notes" -ForegroundColor $colorGreen
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor $colorBlue

$checksumsContent = Get-Content (Join-Path $RELEASE_DIR $checksumFile) | Out-String

$releaseNotesContent = @"
# Sentinel v$VERSION Release Notes

## 🎉 What's New in v1.0.3

This release brings major stability improvements to the long-term running background services on Windows.

### 🌟 Features / Enhancements

- **Windows NSSM Integration**: Both the Sentinel Dashboard and the Probe polling loop are now seamlessly installed and managed securely as authentic Windows Background Services via NSSM. This completely deprecates the old Windows Task Scheduler model for significantly improved reliability and uptime.
- **Headless Dashboard Services**: The start_dashboard.bat natively boots Streamlit in headless mode to prevent unwanted browser execution handles.
- **Continuous Probe Looping**: The run_probe.bat operates dynamically in an infinite 5-minute loop, continuously piping accurate data securely into the backend DB.
- **Automatic Firewall Exclusions**: During setup, port 8501 is seamlessly opened on the Windows Firewall granting out-of-the-box Tailscale and local network accessibility.

### 🐛 Bug Fixes

- **Linux Setup**: Fixed an issue in v1.0.1 where the installation script would rename the entire script directory, breaking the installation flow when the repository files were adjacent.

### Features

- **Real-time Monitoring**: Track hashrate, CPU, and RAM usage across multiple devices
- **P2Pool Integration**: Monitor your P2Pool shares, payouts, and statistics
- **Network Security**: Built-in NIDS (Network Intrusion Detection System) with ARP spoofing detection
- **Multi-Device Support**: Share database across devices using NFS
- **Beautiful Dashboard**: Real-time Streamlit web interface
- **Automatic Hostname Detection**: No more conflicts when monitoring multiple devices
- **Historical Data**: Track performance over time with charts
- **Systemd/NSSM Integration**: Automatic monitoring tools for Linux and Windows
- **SQLite Storage**: Fast, local, no cloud dependencies

### Supported Platforms

- **Linux**: Ubuntu, Debian, Fedora, Arch, and more
- **Windows**: Windows 10, Windows 11

### Installation

#### Linux
```bash
tar -xzf sentinel-linux-v$VERSION.tar.gz
cd sentinel-linux-v$VERSION
chmod +x setup_linux.sh
./setup_linux.sh
```

#### Windows
1. Extract `sentinel-windows-v$VERSION.zip`
2. Double-click `SentinelSetup.bat`
3. Follow the wizard

### Requirements

- Python 3.8+
- XMRig with HTTP API enabled
- (Optional) P2Pool node for P2Pool monitoring
- (Optional) Root access for NIDS functionality

### Documentation

- `README.md` - Complete guide
- `SYSTEMD_SETUP.md` - Systemd service setup (Linux)
- `HOSTNAME_MANAGEMENT.md` - Multi-device configuration
- `DATABASE_SHARING.md` - Database sharing via NFS
- `P2POOL_TROUBLESHOOTING.md` - P2Pool troubleshooting
- `README_LINUX.md` / `README_WINDOWS.md` - Platform-specific guides

### Checksums

```
$($checksumsContent.Trim())
```

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
"@

Set-Content -Path (Join-Path $RELEASE_DIR "RELEASE_NOTES.md") -Value $releaseNotesContent -Encoding utf8

Write-Host "✓ Release notes generated" -ForegroundColor $colorGreen

# ============================================================================
# Summary
# ============================================================================
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor $colorBlue
Write-Host "Release Package Summary" -ForegroundColor $colorGreen
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor $colorBlue
Write-Host ""

Write-Host "Release files created in: $RELEASE_DIR/"
Write-Host ""
Write-Host "Archives:"
Get-ChildItem -Path $RELEASE_DIR -Include *.tar.gz, *.zip | Select-Object Name, @{Name="Size(MB)";Expression={"{0:N2}" -f ($_.Length / 1MB)}} | Format-Table -AutoSize
Write-Host ""
Write-Host "Checksums:"
Get-Content (Join-Path $RELEASE_DIR $checksumFile)
Write-Host ""

Write-Host "✓ Release preparation complete!" -ForegroundColor $colorGreen
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Test the archives on clean systems"
Write-Host "2. Create a GitHub release"
Write-Host "3. Upload the archives and checksums"
Write-Host "4. Copy RELEASE_NOTES.md to GitHub release description"
Write-Host ""
Write-Host "GitHub Release Command:"
Write-Host "  gh release create v$VERSION \"
Write-Host "    $RELEASE_DIR/$PROJECT_NAME-linux-v$VERSION.tar.gz \"
Write-Host "    $RELEASE_DIR/$PROJECT_NAME-windows-v$VERSION.zip \"
Write-Host "    $RELEASE_DIR/$PROJECT_NAME-v$VERSION-checksums.txt \"
Write-Host "    --title `"Sentinel v$VERSION`" \"
Write-Host "    --notes-file $RELEASE_DIR/RELEASE_NOTES.md"
Write-Host ""
