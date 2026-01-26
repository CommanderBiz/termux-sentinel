# Termux-Sentinel

`Termux-Sentinel` is a Python-based tool for monitoring system health, the status of Monero miners, and the security of your local network.

## Features

- **System Monitoring:** Checks local CPU and RAM usage.
- **Miner Probing:** Queries the API of XMRig miners to retrieve the current hashrate.
- **Single Host Check:** Gathers stats from a specific host.
- **Network Scanning:** Scans an entire network range to discover active miners.
- **Intrusion Detection:** Monitors network traffic for suspicious activity (e.g., ARP spoofing).

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/CommanderBiz/termux-sentinel.git
    cd termux-sentinel
    ```

2.  **Install the required Python libraries:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

The `probe.py` script is the core of Sentinel. It can be run in several modes.

### 1. Check a Single Miner

Use the `--host` argument to check a specific machine. If it's a Monero miner, use `--port` to specify the API port.

```bash
python3 probe.py --host 192.168.1.10 --port 8000
```

### 2. Scan the Network for Miners

Use the `--scan` argument with a network range in CIDR notation to find all active miners.

```bash
python3 probe.py --scan 192.168.1.0/24 --port 8000
```

### 3. Run the Network Intrusion Detection System (NIDS)

This mode monitors network traffic for common threats. **This requires root privileges.**

Use the `--nids` flag to start the sniffer. You can specify a network interface with `--iface`.

```bash
sudo python3 probe.py --nids --iface eth0
```

Any detected threats (like ARP spoofing) will be printed to the console and pushed to the Firebase `alerts` collection if configured.
