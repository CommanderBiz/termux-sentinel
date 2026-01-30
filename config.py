#!/usr/bin/env python3
"""
Configuration file for Sentinel monitoring system.
"""

import os

# Database Configuration
DB_PATH = os.path.join(os.path.dirname(__file__), "sentinel.db")

# Miner API Configuration
DEFAULT_MINER_PORT = 8000
MINER_API_TOKEN = "YOUR_API_TOKEN"  # Change this to your actual token
MINER_API_TIMEOUT = 2  # seconds

# P2Pool Configuration
P2POOL_NETWORKS = {
    "main": "https://p2pool.observer/",
    "mini": "https://mini.p2pool.observer/",
    "nano": "https://nano.p2pool.observer/",
}
P2POOL_API_TIMEOUT = 5  # seconds
P2POOL_WINDOW_SIZE = 2160

# Data Retention
# How long to keep historical data (in days)
DATA_RETENTION_DAYS = 30

# Dashboard Configuration
DASHBOARD_REFRESH_INTERVAL = 30  # seconds
DASHBOARD_PORT = 8501  # Default Streamlit port
