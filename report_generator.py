import argparse
import subprocess
import os

def generate_report(host=None, scan_range=None, port=8000):
    """
    Generates a system and Monero miner status report by running probe.py.
    """
    script_path = os.path.join(os.path.dirname(__file__), "probe.py")
    
    command = ["python3", script_path]
    if host:
        command.extend(["--host", host])
    elif scan_range:
        command.extend(["--scan", scan_range])
    else:
        print("Error: Either --host or --scan must be provided.")
        return

    command.extend(["--port", str(port)])

    try:
        print(f"Executing command: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print("Report generation successful.")
        if result.stdout:
            print("Stdout:")
            print(result.stdout)
        if result.stderr:
            print("Stderr:")
            print(result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Error generating report: {e}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
    except FileNotFoundError:
        print(f"Error: probe.py not found at {script_path}. Ensure it exists.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate system and Monero miner status reports.")
    parser.add_argument("--host", help="Hostname or IP address of the miner to check.")
    parser.add_argument("--scan", dest="scan_range", help="Scan a network range in CIDR notation (e.g., 192.168.1.0/24).")
    parser.add_argument("--port", type=int, default=8000, help="API port of the miner(s). Defaults to 8000.")
    args = parser.parse_args()

    generate_report(host=args.host, scan_range=args.scan_range, port=args.port)
