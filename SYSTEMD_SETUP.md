# Sentinel Systemd Service Configuration

This guide explains how to set up Sentinel components as systemd services for automatic startup and management.

## 📋 Overview

Sentinel provides three systemd service files:

1. **sentinel-probe.service** - Periodic miner monitoring
2. **sentinel-dash.service** - Web dashboard (Streamlit)
3. **sentinel-nids.service** - Network intrusion detection (requires root)

## 🔧 Prerequisites

Before setting up services:

```bash
# 1. Ensure all dependencies are installed
pip install -r requirements.txt

# 2. Test that components work manually
python3 probe.py --host 127.0.0.1
python3 app.py
sudo python3 nids.py --iface wlan0

# 3. Note your username and the full path to sentinel directory
whoami
pwd
```

## 🎯 Service 1: Sentinel Probe (with Timer)

The probe service runs periodically to collect miner statistics.

### Step 1: Edit the Service File

Edit `sentinel-probe.service` and update these fields:

```ini
User=your_username           # Replace with your actual username
Group=your_username          # Replace with your actual group
WorkingDirectory=/path/to/sentinel  # Full path to sentinel directory
```

### Step 2: Edit the Timer File

The timer file `sentinel-probe.timer` controls how often the probe runs. The default is every 5 minutes:

```ini
[Timer]
OnBootSec=1min              # Run 1 minute after boot
OnUnitActiveSec=5min        # Run every 5 minutes after that
```

To change frequency, edit `OnUnitActiveSec`:
- Every minute: `1min`
- Every 10 minutes: `10min`
- Every hour: `1h`

### Step 3: Install and Enable

```bash
# Copy service and timer files
sudo cp sentinel-probe.service /etc/systemd/system/
sudo cp sentinel-probe.timer /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable the timer (not the service directly!)
sudo systemctl enable sentinel-probe.timer

# Start the timer
sudo systemctl start sentinel-probe.timer

# Verify it's running
sudo systemctl status sentinel-probe.timer
sudo systemctl list-timers --all | grep sentinel
```

### Step 4: View Logs

```bash
# View probe execution logs
journalctl -u sentinel-probe.service -f

# View timer logs
journalctl -u sentinel-probe.timer -f
```

## 🖥️ Service 2: Sentinel Dashboard

The dashboard provides a web interface for viewing miner statistics.

### Step 1: Edit the Service File

Edit `sentinel-dash.service` and update:

```ini
User=your_username           # Your username
Group=your_username          # Your group
WorkingDirectory=/path/to/sentinel  # Full path
```

Optional: Change the port (default is 8501):
```ini
ExecStart=/usr/bin/python3 -m streamlit run app.py \
    --server.port 8080 \      # Change to your preferred port
```

### Step 2: Install and Enable

```bash
# Copy service file
sudo cp sentinel-dash.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable sentinel-dash.service

# Start the service
sudo systemctl start sentinel-dash.service

# Check status
sudo systemctl status sentinel-dash.service
```

### Step 3: Access Dashboard

Open your browser and navigate to:
- Local: http://localhost:8501
- Remote: http://YOUR_SERVER_IP:8501

### Step 4: View Logs

```bash
# Live logs
journalctl -u sentinel-dash.service -f

# Recent logs
journalctl -u sentinel-dash.service -n 50
```

## 🛡️ Service 3: Sentinel NIDS (Network Intrusion Detection)

NIDS monitors network traffic for security threats. **Requires root privileges.**

### Step 1: Identify Your Network Interface

```bash
# List all network interfaces
ip link show

# or
ifconfig

# Common interface names:
# - eth0, eth1 (Ethernet)
# - wlan0, wlan1 (WiFi)
# - enp0s3, enp0s8 (newer naming)
```

### Step 2: Edit the Service File

Edit `sentinel-nids.service` and update:

```ini
WorkingDirectory=/path/to/sentinel  # Full path

# Update the network interface name (replace wlan0)
ExecStart=/usr/bin/python3 nids.py --iface eth0
```

⚠️ **Important**: NIDS runs as root to capture packets. This is a security consideration.

### Step 3: Install and Enable

```bash
# Copy service file
sudo cp sentinel-nids.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable sentinel-nids.service

# Start the service
sudo systemctl start sentinel-nids.service

# Check status
sudo systemctl status sentinel-nids.service
```

### Step 4: View Logs

```bash
# Live logs
sudo journalctl -u sentinel-nids.service -f

# View recent alerts
python3 nids.py --view-alerts --limit 20
```

## 🔄 Managing Services

### Common Commands

```bash
# Start a service
sudo systemctl start sentinel-dash.service

# Stop a service
sudo systemctl stop sentinel-dash.service

# Restart a service
sudo systemctl restart sentinel-dash.service

# Check service status
sudo systemctl status sentinel-dash.service

# Enable service (start on boot)
sudo systemctl enable sentinel-dash.service

# Disable service (don't start on boot)
sudo systemctl disable sentinel-dash.service

# View logs
journalctl -u sentinel-dash.service -f
```

### For the Timer

```bash
# Start timer
sudo systemctl start sentinel-probe.timer

# Check when next execution is scheduled
sudo systemctl list-timers --all | grep sentinel

# Manually trigger probe (without waiting for timer)
sudo systemctl start sentinel-probe.service
```

## 🧹 Troubleshooting

### Dashboard Won't Start

```bash
# Check if port is already in use
sudo netstat -tulpn | grep 8501

# Check service logs
journalctl -u sentinel-dash.service -n 50

# Test manually
python3 app.py
```

### NIDS Permission Errors

```bash
# Verify NIDS service runs as root
sudo systemctl status sentinel-nids.service | grep "Main PID"

# Check interface exists
ip link show wlan0

# Test manually with sudo
sudo python3 nids.py --iface wlan0
```

### Probe Service Not Running

```bash
# Check timer status
sudo systemctl status sentinel-probe.timer

# View recent executions
journalctl -u sentinel-probe.service -n 50

# Manually trigger
sudo systemctl start sentinel-probe.service

# Check database for updates
python3 probe.py --stats
```

### Database Locked Errors

If multiple services try to write to the database simultaneously:

```bash
# Stop all services temporarily
sudo systemctl stop sentinel-*.service
sudo systemctl stop sentinel-probe.timer

# Check database isn't corrupted
python3 -c "from database import SentinelDB; db = SentinelDB(); print(db.get_database_stats())"

# Restart services one at a time
sudo systemctl start sentinel-probe.timer
sudo systemctl start sentinel-dash.service
sudo systemctl start sentinel-nids.service
```

## 🔒 Security Considerations

### NIDS Running as Root

The NIDS service requires root to capture network packets. To minimize risk:

1. Review the `nids.py` code before running as root
2. Consider using capabilities instead of full root:
   ```bash
   sudo setcap cap_net_raw,cap_net_admin=eip /usr/bin/python3
   ```
3. Monitor NIDS logs regularly for unusual activity

### Dashboard Network Exposure

If accessing the dashboard remotely:

1. Use a reverse proxy with HTTPS (nginx, Apache)
2. Consider adding authentication
3. Use firewall rules to restrict access:
   ```bash
   sudo ufw allow from 192.168.1.0/24 to any port 8501
   ```

### Database Access

Protect the database file:

```bash
chmod 600 /path/to/sentinel/sentinel.db
```

## 📊 Monitoring Services

### Service Health Check Script

Create a simple monitoring script:

```bash
#!/bin/bash
# monitor_sentinel.sh

echo "=== Sentinel Services Status ==="
systemctl is-active sentinel-probe.timer && echo "✅ Probe Timer: Running" || echo "❌ Probe Timer: Stopped"
systemctl is-active sentinel-dash.service && echo "✅ Dashboard: Running" || echo "❌ Dashboard: Stopped"
systemctl is-active sentinel-nids.service && echo "✅ NIDS: Running" || echo "❌ NIDS: Stopped"

echo ""
echo "=== Database Stats ==="
python3 -c "from database import SentinelDB; db = SentinelDB(); print(db.get_database_stats())"
```

Make it executable:
```bash
chmod +x monitor_sentinel.sh
./monitor_sentinel.sh
```

## 📝 Logging Best Practices

### Log Rotation

Prevent logs from filling disk space:

```bash
# Create logrotate config
sudo nano /etc/logrotate.d/sentinel
```

Add:
```
/var/log/sentinel/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

## 🆘 Getting Help

If you encounter issues:

1. Check service status: `sudo systemctl status sentinel-*.service`
2. Review logs: `journalctl -u sentinel-dash.service -n 100`
3. Test components manually without systemd
4. Verify all paths and usernames in service files
5. Ensure all dependencies are installed

---

## Quick Reference Card

```bash
# Start everything
sudo systemctl start sentinel-probe.timer
sudo systemctl start sentinel-dash.service
sudo systemctl start sentinel-nids.service

# Stop everything
sudo systemctl stop sentinel-probe.timer
sudo systemctl stop sentinel-dash.service
sudo systemctl stop sentinel-nids.service

# View all logs together
journalctl -u sentinel-* -f

# Check what's running
systemctl list-units sentinel-*
```
