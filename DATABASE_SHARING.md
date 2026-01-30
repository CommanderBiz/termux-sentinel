# Database Sharing Solutions for Multi-Device Sentinel Setup

When running Sentinel on multiple devices, you have several options for sharing the database:

## 📊 The Challenge

Each device currently has its own `sentinel.db` file. Device A can't see Device B's miners, and vice versa.

## 🎯 Solutions (Ranked by Complexity)

---

## Option 1: Network File Share (NFS/SMB) - SIMPLEST ⭐ RECOMMENDED

Share the database file over your network using NFS (Linux) or SMB/CIFS (cross-platform).

### Method A: NFS (Linux-to-Linux)

**On the "main" device (database host):**

```bash
# 1. Install NFS server
sudo apt-get install nfs-kernel-server

# 2. Create shared directory
sudo mkdir -p /opt/sentinel-shared
sudo chown your_username:your_username /opt/sentinel-shared

# 3. Move database there
mv /path/to/sentinel/sentinel.db /opt/sentinel-shared/

# 4. Export the directory
sudo nano /etc/exports
```

Add this line:
```
/opt/sentinel-shared 192.168.1.0/24(rw,sync,no_subtree_check)
```

```bash
# 5. Apply changes
sudo exportfs -ra
sudo systemctl restart nfs-kernel-server
```

**On secondary devices:**

```bash
# 1. Install NFS client
sudo apt-get install nfs-common

# 2. Create mount point
sudo mkdir -p /opt/sentinel-shared

# 3. Mount the share
sudo mount 192.168.1.100:/opt/sentinel-shared /opt/sentinel-shared

# 4. Make it permanent (add to /etc/fstab)
echo "192.168.1.100:/opt/sentinel-shared /opt/sentinel-shared nfs defaults 0 0" | sudo tee -a /etc/fstab

# 5. Update config.py to point to shared DB
nano /path/to/sentinel/config.py
```

Change in `config.py`:
```python
DB_PATH = "/opt/sentinel-shared/sentinel.db"
```

**Pros:**
- Simple setup
- Native Linux support
- Good performance on local network
- All devices see same data instantly

**Cons:**
- Requires one device to be always on
- Network dependency
- File locking can be tricky with SQLite over NFS

---

## Option 2: SMB/CIFS Share (Cross-Platform) - WINDOWS FRIENDLY

Use SMB for Windows/Linux mixed environments.

**On Windows (database host):**

1. Create folder: `C:\sentinel-shared`
2. Right-click → Properties → Sharing → Advanced Sharing
3. Check "Share this folder"
4. Set permissions (Everyone: Read/Write)
5. Note the share path: `\\YOUR-PC\sentinel-shared`

**On Linux devices:**

```bash
# Install CIFS utilities
sudo apt-get install cifs-utils

# Create mount point
sudo mkdir -p /mnt/sentinel-shared

# Mount the Windows share
sudo mount -t cifs //192.168.1.100/sentinel-shared /mnt/sentinel-shared -o username=your_windows_user,password=your_password

# Make permanent (credentials file for security)
sudo nano /etc/samba-credentials
```

Add:
```
username=your_windows_user
password=your_password
```

```bash
sudo chmod 600 /etc/samba-credentials

# Add to /etc/fstab
echo "//192.168.1.100/sentinel-shared /mnt/sentinel-shared cifs credentials=/etc/samba-credentials,uid=1000,gid=1000 0 0" | sudo tee -a /etc/fstab

# Update config.py
DB_PATH = "/mnt/sentinel-shared/sentinel.db"
```

**Pros:**
- Works with Windows/Linux/Mac
- Easy to set up on Windows
- Good for mixed environments

**Cons:**
- Slightly slower than NFS
- Requires credentials management
- Same file locking concerns as NFS

---

## Option 3: Sync Tool (Syncthing) - NO SERVER NEEDED

Use Syncthing to keep databases synchronized between devices without a central server.

**Setup:**

```bash
# Install Syncthing on all devices
# Ubuntu/Debian:
sudo apt-get install syncthing

# Start Syncthing
syncthing

# Access web UI at http://localhost:8384
```

**Configuration:**

1. On each device, add the `/path/to/sentinel` folder
2. Share with other devices
3. Enable "Ignore Delete" to prevent accidental wipes
4. Set sync interval to 60 seconds

**Important SQLite Consideration:**

Since SQLite doesn't handle concurrent writes well over sync:

```bash
# On each device, modify the systemd timer to NOT overlap
# Device 1: Run at :00, :05, :10, :15 (every 5 min starting at :00)
# Device 2: Run at :02, :07, :12, :17 (every 5 min starting at :02)
```

**Pros:**
- No central server needed
- Peer-to-peer sync
- Works even when devices aren't all online
- Encrypted transfer

**Cons:**
- More complex setup
- Requires careful scheduling to avoid conflicts
- Sync delays (not instant)
- Risk of database corruption with concurrent writes

---

## Option 4: Centralized Database Server - MOST ROBUST 🏆 BEST FOR 3+ DEVICES

Replace SQLite with PostgreSQL or MySQL on a central server.

This requires significant code changes but gives you a true multi-device setup.

**I can create this for you if you want!** It would involve:
- Setting up PostgreSQL/MySQL
- Modifying `database.py` to use PostgreSQL instead of SQLite
- All devices connect to central DB server
- Better concurrent write handling
- Proper transaction management

---

## ⚠️ SQLite File Locking Warning

SQLite is designed for single-device use. When sharing over network:

### The Problem:
Multiple devices writing simultaneously can cause:
- Database corruption
- "Database is locked" errors
- Data loss

### Solutions:

**A) Write Coordination (Use with NFS/SMB)**

Stagger the probe timers so devices never write simultaneously:

```bash
# Device 1: sentinel-probe.timer
[Timer]
OnBootSec=1min
OnUnitActiveSec=10min  # Every 10 minutes starting at :00

# Device 2: sentinel-probe.timer  
[Timer]
OnBootSec=3min
OnUnitActiveSec=10min  # Every 10 minutes starting at :02

# Device 3: sentinel-probe.timer
[Timer]
OnBootSec=5min
OnUnitActiveSec=10min  # Every 10 minutes starting at :04
```

**B) Use WAL Mode (Write-Ahead Logging)**

Enable WAL mode in SQLite for better concurrent access:

Add to `database.py` in the `initialize_database()` method:

```python
# Enable WAL mode for better concurrent access
cursor.execute("PRAGMA journal_mode=WAL")
cursor.execute("PRAGMA busy_timeout=5000")  # Wait 5 seconds if locked
```

**C) Designate One "Writer" Device**

- One device runs the probe (collects data)
- Other devices only run the dashboard (read-only)
- Simplest solution for 2 devices!

---

## 🎯 My Recommendation for Your 2-Device Setup

**Best approach: NFS + Write Coordination + WAL Mode**

```bash
# 1. Set up NFS share on Device 1 (see Option 1)

# 2. Mount on Device 2

# 3. Enable WAL mode (I'll create updated database.py)

# 4. Stagger probe timers:
#    Device 1: Runs at :00, :05, :10, :15, :20...
#    Device 2: Runs at :02, :07, :12, :17, :22...

# 5. Both devices can run dashboards (read-only is safe)
```

This gives you:
- Shared database (instant updates)
- Minimal conflict risk
- Simple setup
- Both devices can monitor

---

## 🔨 Quick Implementation

Want me to create:

1. **NFS setup scripts** - Automated NFS configuration
2. **Updated database.py** - With WAL mode and better locking
3. **Staggered timer configs** - Pre-configured for Device 1 & 2
4. **PostgreSQL migration** - Full database server setup (if you want enterprise-grade)

Which option sounds best for your needs?

---

## 📊 Comparison Table

| Solution | Setup Complexity | Performance | Reliability | Concurrent Writes | Best For |
|----------|-----------------|-------------|-------------|-------------------|----------|
| NFS Share | ⭐⭐ Medium | ⚡⚡⚡ Fast | ⭐⭐⭐ Good* | ⚠️ Risky | 2-3 Linux devices |
| SMB/CIFS | ⭐ Easy | ⚡⚡ Medium | ⭐⭐ OK* | ⚠️ Risky | Mixed OS |
| Syncthing | ⭐⭐⭐ Complex | ⚡⚡ Medium | ⭐⭐⭐⭐ Great | ⚠️ Must schedule | No server |
| PostgreSQL | ⭐⭐⭐⭐ Hard | ⚡⚡⚡ Fast | ⭐⭐⭐⭐⭐ Best | ✅ Safe | 3+ devices |

*With proper write coordination

---

## 🚀 Quick Start: 2-Device NFS Setup (5 minutes)

**Device 1 (192.168.1.100 - Main/Host):**

```bash
sudo apt-get install -y nfs-kernel-server
sudo mkdir -p /opt/sentinel-shared
sudo mv ~/sentinel/sentinel.db /opt/sentinel-shared/
echo "/opt/sentinel-shared 192.168.1.0/24(rw,sync,no_subtree_check)" | sudo tee -a /etc/exports
sudo exportfs -ra
sudo systemctl restart nfs-kernel-server

# Update config
sed -i 's|DB_PATH = .*|DB_PATH = "/opt/sentinel-shared/sentinel.db"|' ~/sentinel/config.py
```

**Device 2 (Secondary):**

```bash
sudo apt-get install -y nfs-common
sudo mkdir -p /opt/sentinel-shared
sudo mount 192.168.1.100:/opt/sentinel-shared /opt/sentinel-shared
echo "192.168.1.100:/opt/sentinel-shared /opt/sentinel-shared nfs defaults 0 0" | sudo tee -a /etc/fstab

# Update config
sed -i 's|DB_PATH = .*|DB_PATH = "/opt/sentinel-shared/sentinel.db"|' ~/sentinel/config.py

# Stagger timer (run 2 minutes after Device 1)
sudo sed -i 's/OnBootSec=1min/OnBootSec=3min/' /etc/systemd/system/sentinel-probe.timer
sudo systemctl daemon-reload
sudo systemctl restart sentinel-probe.timer
```

Done! Both devices now share the same database.

---

Let me know which approach you'd like and I can create the specific files/scripts you need!
