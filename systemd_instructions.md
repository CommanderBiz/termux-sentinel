This file (`sentinel-dash.service`) has been created for you to configure a systemd service.

**Important:** Before using this file, please ensure you replace `s3nok` with your actual username and group in the `User` and `Group` fields.

## Sentinel Dashboard Service (`sentinel-dash.service`)

To use this service file:

1.  **Move the service file:**
    ```bash
    sudo mv sentinel-dash.service /etc/systemd/system/
    ```
    This moves the service definition to the systemd directory.

2.  **Reload `systemd` to pick up the new service:**
    ```bash
    sudo systemctl daemon-reload
    ```

3.  **Enable the service to start on boot:**
    ```bash
    sudo systemctl enable sentinel-dash.service
    ```

4.  **Start the service:**
    ```bash
    sudo systemctl start sentinel-dash.service
    ```

5.  **Check the status of the service (optional, for debugging):**
    ```bash
    sudo systemctl status sentinel-dash.service
    ```
    or to view logs:
    ```bash
    journalctl -u sentinel-dash.service -f
    ```

## Sentinel Probe Service (`sentinel-probe.service`)

This service runs `probe.py` to periodically scan your network for miners and push their status to Firebase.

To use this service file:

1.  **Move the service file:**
    ```bash
    sudo mv sentinel-probe.service /etc/systemd/system/
    ```

2.  **Reload `systemd` to pick up the new service:**
    ```bash
    sudo systemctl daemon-reload
    ```

3.  **Enable the service to start on boot:**
    ```bash
    sudo systemctl enable sentinel-probe.service
    ```

4.  **Start the service:**
    ```bash
    sudo systemctl start sentinel-probe.service
    ```

5.  **Check the status of the service:**
    ```bash
    sudo systemctl status sentinel-probe.service
    ```
    or to view logs:
    ```bash
    journalctl -u sentinel-probe.service -f
    ```

## Sentinel NIDS Service (`sentinel-nids.service`)

This service runs the Network Intrusion Detection System to monitor for threats like ARP spoofing. **This service must be run as root.**

To use this service file:

1.  **Move the service file:**
    ```bash
    sudo mv sentinel-nids.service /etc/systemd/system/
    ```

2.  **Reload `systemd` to pick up the new service:**
    ```bash
    sudo systemctl daemon-reload
    ```

3.  **Enable the service to start on boot:**
    ```bash
    sudo systemctl enable sentinel-nids.service
    ```

4.  **Start the service:**
    ```bash
    sudo systemctl start sentinel-nids.service
    ```

5.  **Check the status of the service:**
    ```bash
    sudo systemctl status sentinel-nids.service
    ```
    or to view logs:
    ```bash
    sudo journalctl -u sentinel-nids.service -f
    ```

## On-demand Status Reports (`report_generator.py`)

The `report_generator.py` script allows you to manually trigger a scan and push updates to Firebase. This is useful for immediate checks or specific debugging.

**Usage:**

To check a specific host:
```bash
python3 /home/s3nok/termux-sentinel/report_generator.py --host 192.168.1.100 --port 8000
```

To scan a network range:
```bash
python3 /home/s3nok/termux-sentinel/report_generator.py --scan 192.168.1.0/24 --port 8000
```

You can omit `--port` if your miner(s) use the default port 8000.
