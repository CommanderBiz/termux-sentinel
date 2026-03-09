@echo off
cd /d "C:\path\to\sentinel"
"C:\path\to\sentinel\venv\Scripts\python.exe" -m streamlit run app.py --server.address=0.0.0.0 --server.headless=true > "C:\path\to\sentinel\dashboard_service.log" 2>&1
pause
