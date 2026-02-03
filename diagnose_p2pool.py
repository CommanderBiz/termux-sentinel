#!/usr/bin/env python3
"""
P2Pool Diagnostic Tool
Tests P2Pool API connectivity and shows detailed stats
"""

import requests
import argparse
import json
from datetime import datetime

P2POOL_NETWORKS = {
    "main": "https://p2pool.observer/",
    "mini": "https://mini.p2pool.observer/",
    "nano": "https://nano.p2pool.observer/",
}

def diagnose_p2pool(miner_address, network="main"):
    """Run comprehensive P2Pool diagnostics."""
    
    base_url = P2POOL_NETWORKS.get(network, P2POOL_NETWORKS["main"])
    
    print("="*70)
    print(f"🔍 P2Pool Diagnostic Tool")
    print("="*70)
    print(f"Network: {network}")
    print(f"Base URL: {base_url}")
    print(f"Miner Address: {miner_address}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    print()
    
    # Test 1: Check if address is valid format
    print("📋 Test 1: Address Validation")
    if len(miner_address) == 95 or len(miner_address) == 106:  # Standard or integrated
        print(f"  ✅ Address length valid: {len(miner_address)} chars")
    else:
        print(f"  ⚠️  Address length unusual: {len(miner_address)} chars (expected 95 or 106)")
    
    if miner_address.startswith('4'):
        print(f"  ✅ Starts with '4' (Mainnet address)")
    else:
        print(f"  ⚠️  Address doesn't start with '4' (testnet/stagenet?)")
    print()
    
    # Test 2: Query miner_info
    print("📋 Test 2: Miner Info API")
    info_url = f"{base_url}api/miner_info/{miner_address}"
    print(f"  URL: {info_url}")
    
    try:
        info_resp = requests.get(info_url, timeout=10)
        print(f"  Status Code: {info_resp.status_code}")
        
        if info_resp.status_code == 200:
            print(f"  ✅ Successfully retrieved miner info")
            info_data = info_resp.json()
            
            # Show raw response
            print(f"\n  📄 Raw Response:")
            print(f"  {json.dumps(info_data, indent=4)}")
            print()
            
            # Parse shares array
            shares_data = info_data.get('shares', [])
            print(f"  📊 Shares Array Length: {len(shares_data)}")
            
            if len(shares_data) > 0:
                print(f"  Index 0 (Window): {shares_data[0]}")
            if len(shares_data) > 1:
                print(f"  Index 1 (Total): {shares_data[1]}")
            
            # Check last share time
            last_share_time = info_data.get('last_share_time')
            if last_share_time:
                print(f"\n  ⏰ Last Share Time: {last_share_time}")
            else:
                print(f"\n  ⚠️  No last_share_time found")
                
        else:
            print(f"  ❌ API returned status {info_resp.status_code}")
            print(f"  Response: {info_resp.text}")
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
    print()
    
    # Test 3: Query recent shares
    print("📋 Test 3: Recent Shares API")
    shares_url = f"{base_url}api/shares?miner={miner_address}"
    print(f"  URL: {shares_url}")
    
    try:
        shares_resp = requests.get(shares_url, timeout=10)
        print(f"  Status Code: {shares_resp.status_code}")
        
        if shares_resp.status_code == 200:
            shares = shares_resp.json()
            print(f"  ✅ Found {len(shares)} share(s)")
            
            if shares:
                print(f"\n  📄 Recent Shares:")
                for i, share in enumerate(shares[:5], 1):  # Show first 5
                    height = share.get('side_height', 'N/A')
                    timestamp = share.get('timestamp', 'N/A')
                    uncle = share.get('uncle', False)
                    print(f"    {i}. Height: {height} | Time: {timestamp} | Uncle: {uncle}")
                
                if len(shares) > 5:
                    print(f"    ... and {len(shares) - 5} more")
            else:
                print(f"  ⚠️  No shares found for this address")
                print(f"  This could mean:")
                print(f"    - You haven't found a share yet")
                print(f"    - Wrong network (try --network mini)")
                print(f"    - Wrong address")
        else:
            print(f"  ❌ API returned status {shares_resp.status_code}")
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
    print()
    
    # Test 4: Get current pool height
    print("📋 Test 4: Pool Status")
    pool_url = f"{base_url}api/pool/stats"
    print(f"  URL: {pool_url}")
    
    try:
        pool_resp = requests.get(pool_url, timeout=10)
        if pool_resp.status_code == 200:
            pool_data = pool_resp.json()
            print(f"  ✅ Pool stats retrieved")
            print(f"  Pool Hashrate: {pool_data.get('pool_statistics', {}).get('hashRate', 'N/A')}")
            print(f"  Miners: {pool_data.get('pool_statistics', {}).get('miners', 'N/A')}")
            print(f"  Total Hashes: {pool_data.get('pool_statistics', {}).get('totalHashes', 'N/A')}")
        else:
            print(f"  ⚠️  Could not get pool stats (status {pool_resp.status_code})")
    except Exception as e:
        print(f"  ⚠️  Error: {e}")
    print()
    
    # Test 5: Check latest network share
    print("📋 Test 5: Latest Network Share")
    latest_url = f"{base_url}api/shares?limit=1"
    print(f"  URL: {latest_url}")
    
    try:
        latest_resp = requests.get(latest_url, timeout=10)
        if latest_resp.status_code == 200:
            latest = latest_resp.json()
            if latest:
                print(f"  ✅ Latest share on network:")
                print(f"     Height: {latest[0].get('side_height')}")
                print(f"     Time: {latest[0].get('timestamp')}")
                print(f"     Miner: {latest[0].get('miner', 'N/A')[:20]}...")
            else:
                print(f"  ⚠️  No shares on network yet")
        else:
            print(f"  ❌ Error: Status {latest_resp.status_code}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    print()
    
    # Test 6: Check payouts
    print("📋 Test 6: Payouts")
    payouts_url = f"{base_url}api/payouts?miner={miner_address}"
    print(f"  URL: {payouts_url}")
    
    try:
        payouts_resp = requests.get(payouts_url, timeout=10)
        if payouts_resp.status_code == 200:
            payouts = payouts_resp.json()
            print(f"  ✅ Found {len(payouts)} payout(s)")
            
            if payouts:
                print(f"\n  💰 Recent Payouts:")
                for i, payout in enumerate(payouts[:5], 1):  # Show first 5
                    amount = payout.get('value', 0) / 1e12  # Convert to XMR
                    timestamp = payout.get('timestamp', 'N/A')
                    height = payout.get('height', 'N/A')
                    print(f"    {i}. Amount: {amount:.8f} XMR | Time: {timestamp} | Height: {height}")
                
                if len(payouts) > 5:
                    print(f"    ... and {len(payouts) - 5} more")
                    
                # Calculate total
                total_xmr = sum(p.get('value', 0) for p in payouts) / 1e12
                print(f"\n  💎 Total Paid: {total_xmr:.8f} XMR")
            else:
                print(f"  ⚠️  No payouts found yet")
                print(f"  This is normal if you haven't received a payout yet.")
        else:
            print(f"  ❌ API returned status {payouts_resp.status_code}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    print()
    
    print("="*70)
    print("🔍 Diagnostic Complete")
    print("="*70)
    print()
    print("💡 Next Steps:")
    print("   1. If no shares found, verify:")
    print("      - Correct network (main/mini/nano)")
    print("      - Address is correct")
    print("      - You've actually found a share")
    print()
    print("   2. If shares found but not in Sentinel:")
    print("      - Run: python3 probe.py --host 127.0.0.1 --p2pool-miner-address YOUR_ADDRESS")
    print("      - Check: python3 probe.py --stats")
    print("      - View dashboard: streamlit run app.py")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Diagnose P2Pool API connectivity and miner stats"
    )
    parser.add_argument(
        "address",
        help="Your Monero wallet address"
    )
    parser.add_argument(
        "--network",
        choices=["main", "mini", "nano"],
        default="main",
        help="P2Pool network (default: main)"
    )
    
    args = parser.parse_args()
    diagnose_p2pool(args.address, args.network)
    