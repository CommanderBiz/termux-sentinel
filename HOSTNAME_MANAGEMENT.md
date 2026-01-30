# Multi-Device Hostname Management Guide

## 🔍 The Problem

When running `probe.py --host 127.0.0.1` on multiple devices:
- Device 1 writes stats with host="127.0.0.1"
- Device 2 writes stats with host="127.0.0.1"
- **They overwrite each other!** Only one device's data shows in the dashboard.

## ✅ The Solution

Sentinel now **automatically detects hostnames** when monitoring localhost, preventing conflicts.

---

## 🎯 How It Works

### Automatic Hostname Detection

When you run:
```bash
python3 probe.py --host 127.0.0.1
```

Sentinel automatically:
1. Detects you're monitoring localhost
2. Uses the actual hostname (e.g., `mini0`, `laptop`) instead of `127.0.0.1`
3. Stores data with the unique hostname
4. Collects CPU and RAM stats (because it's local)

**Result:** Each device appears separately in the dashboard with full stats!

---

## 📋 Usage Examples

### Option 1: Automatic (Recommended)

Simply use `127.0.0.1` on each device:

**Device 1 (hostname: mini0):**
```bash
python3 probe.py --host 127.0.0.1
# Automatically stored as: mini0
```

**Device 2 (hostname: laptop):**
```bash
python3 probe.py --host 127.0.0.1
# Automatically stored as: laptop
```

**Dashboard shows:**
- ✅ mini0 - 1250 H/s - CPU: 85% - RAM: 60%
- ✅ laptop - 850 H/s - CPU: 70% - RAM: 45%

### Option 2: Custom Names

Use the `--name` parameter for friendly names:

**Device 1:**
```bash
python3 probe.py --host 127.0.0.1 --name "Mining Rig 1"
# Stored as: Mining Rig 1
```

**Device 2:**
```bash
python3 probe.py --host 127.0.0.1 --name "My Laptop"
# Stored as: My Laptop
```

**Dashboard shows:**
- ✅ Mining Rig 1 - 1250 H/s - CPU: 85% - RAM: 60%
- ✅ My Laptop - 850 H/s - CPU: 70% - RAM: 45%

### Option 3: Mix and Match

You can still monitor remote devices by IP:

**Device 1 monitors itself + remote device:**
```bash
# Monitor self with auto-detection
python3 probe.py --host 127.0.0.1

# Monitor remote device (no CPU/RAM stats)
python3 probe.py --host 192.168.1.50
```

**Dashboard shows:**
- ✅ mini0 - 1250 H/s - CPU: 85% - RAM: 60%
- ✅ 192.168.1.50 - 950 H/s

---

## 🔧 Systemd Service Configuration

### Update Your Service Files

If you've already set up systemd services, you have two options:

#### Option A: Use Automatic Detection (No changes needed!)

Your existing service file works as-is:
```ini
ExecStart=/usr/bin/python3 probe.py --host 127.0.0.1
```

Each device will automatically use its hostname.

#### Option B: Use Custom Names

Edit your service file on each device:

**On Device 1 (`/etc/systemd/system/sentinel-probe.service`):**
```ini
ExecStart=/usr/bin/python3 probe.py --host 127.0.0.1 --name "mining-rig-1"
```

**On Device 2:**
```ini
ExecStart=/usr/bin/python3 probe.py --host 127.0.0.1 --name "mining-laptop"
```

Then reload:
```bash
sudo systemctl daemon-reload
sudo systemctl restart sentinel-probe.timer
```

---

## 📊 Dashboard Display

Your dashboard will now show each device separately:

```
🛡️ Sentinel Dashboard
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Miners: 2    Online: 2    Total Hashrate: 2100 H/s

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─────────────────────────────────────────────┐
│ Host: mini0                                 │
│ ✓ Online - Hashrate: 1250.00 H/s          │
│ Last seen: 2m ago                          │
│ CPU Usage: 85%    RAM Usage: 60%          │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ Host: laptop                                │
│ ✓ Online - Hashrate: 850.00 H/s           │
│ Last seen: Just now                        │
│ CPU Usage: 70%    RAM Usage: 45%          │
└─────────────────────────────────────────────┘
```

---

## 🏷️ Setting Device Hostnames

If you want cleaner hostnames, you can change them on your devices:

### Linux (Permanent)

```bash
# Check current hostname
hostname

# Set new hostname
sudo hostnamectl set-hostname mini0

# Or edit directly
sudo nano /etc/hostname
# Change to: mini0

sudo reboot
```

### Termux (Android)

```bash
# Set hostname for current session
hostname mini0

# Make permanent (add to ~/.bashrc)
echo 'hostname mini0' >> ~/.bashrc
```

### Common Naming Schemes

Choose a naming pattern that works for you:

**By Device Type:**
- `desktop-mining`, `laptop-mining`, `raspberry-pi`

**By Location:**
- `office-miner`, `bedroom-miner`, `garage-rig`

**By Number:**
- `miner-01`, `miner-02`, `miner-03`

**By Specs:**
- `8core-rig`, `threadripper`, `i7-laptop`

---

## 🔄 Migration from Old Setup

If you already have data with `127.0.0.1` entries:

### Option 1: Start Fresh (Easiest)

```bash
# Backup old database
cp sentinel.db sentinel.db.old

# Remove localhost entries
python3 -c "
from database import SentinelDB
db = SentinelDB()
import sqlite3
conn = sqlite3.connect('sentinel.db')
cursor = conn.cursor()
cursor.execute('DELETE FROM miners WHERE host = \"127.0.0.1\"')
cursor.execute('DELETE FROM miner_history WHERE host = \"127.0.0.1\"')
conn.commit()
conn.close()
print('Cleaned up localhost entries')
"

# Run probe again
python3 probe.py --host 127.0.0.1
```

### Option 2: Rename Existing Entries

If you want to keep historical data:

```bash
# Get current hostname
HOSTNAME=$(hostname)

# Rename entries in database
python3 -c "
import sqlite3
hostname = '${HOSTNAME}'
conn = sqlite3.connect('sentinel.db')
cursor = conn.cursor()
cursor.execute('UPDATE miners SET host = ? WHERE host = \"127.0.0.1\"', (hostname,))
cursor.execute('UPDATE miner_history SET host = ? WHERE host = \"127.0.0.1\"', (hostname,))
conn.commit()
print(f'Renamed 127.0.0.1 entries to {hostname}')
conn.close()
"
```

---

## 🧪 Testing

Verify everything works:

### 1. Check Automatic Detection

```bash
python3 probe.py --host 127.0.0.1
# Should show: "Local host detected, using hostname: YOUR_HOSTNAME"
```

### 2. Check Database

```bash
python3 probe.py --stats
# Should show your hostname, not 127.0.0.1
```

### 3. View in Dashboard

```bash
streamlit run app.py
# Navigate to http://localhost:8501
# You should see your device with hostname
```

### 4. Test Custom Name

```bash
python3 probe.py --host 127.0.0.1 --name "Test Rig"
# Should show: "Using custom name: Test Rig"

# Check it's in database
python3 probe.py --stats
```

---

## 💡 Pro Tips

### 1. Consistent Naming

Pick a naming scheme and stick to it across all devices:
```bash
# Device 1
--name "rig-01"

# Device 2
--name "rig-02"
```

### 2. Include Location in Name

Helpful for large setups:
```bash
--name "basement-rig-1"
--name "office-laptop"
--name "garage-threadripper"
```

### 3. Monitor Multiple Miners per Device

Some devices run multiple miners:
```bash
# Monitor local XMRig
python3 probe.py --host 127.0.0.1 --port 8000 --name "laptop-xmrig"

# Monitor local p2pool node
python3 probe.py --host 127.0.0.1 --port 3333 --name "laptop-p2pool"
```

### 4. Use Cron for Monitoring

Set up different schedules for different devices:

**Device 1 - Heavy miner (check frequently):**
```bash
# Every 2 minutes
*/2 * * * * /usr/bin/python3 /path/to/probe.py --host 127.0.0.1
```

**Device 2 - Light miner (check less often):**
```bash
# Every 10 minutes
*/10 * * * * /usr/bin/python3 /path/to/probe.py --host 127.0.0.1
```

---

## ❓ FAQ

**Q: What if two devices have the same hostname?**

A: Use `--name` to give them unique identifiers:
```bash
# Device 1
--name "mini0-bedroom"

# Device 2
--name "mini0-office"
```

**Q: Can I change the name later?**

A: Yes! Just use a different `--name` value. The old entry will become stale and you can clean it up:
```bash
python3 probe.py --cleanup
```

**Q: Will this work with the shared database (NFS)?**

A: Yes! That's the whole point. Each device will have its own entry in the shared database.

**Q: Do I need to restart services?**

A: Only if you're changing systemd service files. Otherwise, the next probe run will use the new logic automatically.

**Q: What about network scans?**

A: Network scans (`--scan`) use IP addresses as-is. This feature only affects `--host 127.0.0.1` / `--host localhost`.

---

## 🎉 Benefits Summary

✅ **No more conflicts** - Each device has unique identity
✅ **Automatic detection** - Works without configuration  
✅ **CPU/RAM stats** - Full system monitoring for all devices
✅ **Custom names** - Friendly, readable device names
✅ **NFS compatible** - Works perfectly with shared database
✅ **Zero downtime** - Update with no service interruption

---

## 🚀 Quick Setup Checklist

- [ ] Update `probe.py` to latest version
- [ ] Test: `python3 probe.py --host 127.0.0.1`
- [ ] Verify hostname in output
- [ ] Update systemd services (optional)
- [ ] Clean up old `127.0.0.1` entries (optional)
- [ ] Check dashboard shows all devices
- [ ] Set up monitoring on remaining devices

---

**Your multi-device setup is now ready! Each device will appear separately with full stats.** 🎊
