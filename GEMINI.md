# Gemini Project Memory

## Project Checkpoint: 2026-02-15 (Payout Tracking Fixes & Improvements)
- **Fixed Payout Count Limit**: Increased API query limit from 10 to 1000 in `probe.py` to ensure "Total Payouts" doesn't get stuck.
- **Enhanced Payout Tracking**: Added `total_payout_amount` to database schema and probe logic to track cumulative XMR earned.
- **Dashboard Updates**: Modified `app.py` to display the total XMR amount alongside the payout count.
- **Diagnostic Tool Fixes**: Corrected `diagnose_p2pool.py` API endpoints and fixed a bug where integer miner IDs caused crashes.
- **Database Migration**: Successfully added `total_payout_amount` column to `p2pool_stats` table.

## Project Checkpoint: 2026-02-08 (P2Pool API Fixes & Payout Tracking)
- **P2Pool Integration Fixes**:
    - Corrected API endpoints in `probe.py` for fetching blocks (`api/found_blocks`) and payouts (`api/payouts/{address}`).
    - Fixed field mapping for payout amount (switched from `value` to `coinbase_reward`).
- **Feature Addition: Payout Detail Tracking**:
    - **Database**: Added automatic schema migration to include `last_payout_amount` and `last_payout_time` in `p2pool_stats` table.
    - **Probe**: Updated logic to capture and store the latest payout amount and timestamp.
    - **Dashboard**: Enhanced P2Pool section to display "Last Payout" amount and time-ago formatted timestamp.
- **Service Status**:
    - Restarted `sentinel-probe` and `sentinel-dash` services to apply changes.
    - Verified correct data fetching from P2Pool Nano network.

## Project Checkpoint: 2026-02-02 (Maintenance & Sync)
- **Repository Synchronization**:
    - Pulled latest changes from remote repository.
    - Resolved merge conflicts in `app.py` (preserved local "Delete Host" UI feature) and `GEMINI.md`.
    - Integrated new documentation and setup scripts (`setup_linux.sh`, `PAYOUT_TRACKING.md`, etc.) from the remote.
- **Service Maintenance**:
    - Successfully stopped, updated, and restarted `sentinel-dash`, `sentinel-nids`, and `sentinel-probe.timer`.
    - Verified all services are active and running after the update.
    - Re-applied and verified dependencies in the local `venv`.

## Project Checkpoint: 2026-01-30 (NFS & Network Stabilization)
- **P2Pool Network Transition**:
    - Successfully switched monitoring from `mini` to `nano` network.
    - Verified wallet address `48tqgAhkjCnV2AUoTc5QztTrKSn1KVzvcHJ931sV2zWRG5MbMoipXAUBdY3JLn7SMRDLmTCCwa64ZHFqnThAwwzK1RhJM7W`.
- **Shared Database Infrastructure**:
    - Configured NFS Server on `mini0` (192.168.1.91).
    - Database moved to `/opt/sentinel-shared/sentinel.db` for multi-device access.
    - Updated `config.py` with `MINER_API_TOKEN="Mugiwara!0"` and new `DB_PATH`.
- **Systemd & Service Stability**:
    - Synchronized all local `.service` files with `/etc/systemd/system/`.
    - `sentinel-probe.timer`, `sentinel-dash.service`, and `sentinel-nids.service` are active and verified.
    - NFS setup scripts (`setup_nfs_server.sh`, `setup_nfs_client.sh`) updated with absolute paths and executable permissions.

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
