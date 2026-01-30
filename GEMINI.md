# Gemini Project Memory

## Project Checkpoint: 2026-01-29 (Fixes)
- **Service Stability**:
    - Created local Python virtual environment (`venv`) to isolate dependencies.
    - Updated `sentinel-dash`, `sentinel-nids`, and `sentinel-probe` systemd services to use the `venv` Python executable.
    - Fixed `sentinel-probe` 404 error by switching P2Pool network target to `mini`.
- **Git Status**:
    - Service file fixes committed.
    - Push to remote failed (DNS/Network issue), pending manual push.

## Project Checkpoint: 2026-01-29
- **Systemd Setup Complete**:
    - `sentinel-probe.timer`: Configured with P2Pool address `48tqgAhkjCnV2AUoTc5QztTrKSn1KVzvcHJ931sV2zWRG5MbMoipXAUBdY3JLn7SMRDLmTCCwa64ZHFqnThAwwzK1RhJM7W`.
    - `sentinel-nids.service`: Configured to use network interface `eno1`.
    - `sentinel-dash.service`: Running on default port 8501.
- **Git Status**:
    - All service files and configuration updates have been committed and pushed to `main`.
    - Repo is clean.