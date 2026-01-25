This file (`sentinel-dash.service`) has been created for you to configure a systemd service.

**Important:** Before using this file, please ensure you replace `s3nok` with your actual username and group in the `User` and `Group` fields.

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
