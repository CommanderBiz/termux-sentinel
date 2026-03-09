@echo off
cd /d "C:\path\to\sentinel"

:loop
"C:\path\to\sentinel\venv\Scripts\python.exe" probe.py --host 127.0.0.1 --port 8000 --p2pool-miner-address YOUR_WALLET_ADDRESS --p2pool-network main
timeout /t 300 /nobreak > nul
goto loop
