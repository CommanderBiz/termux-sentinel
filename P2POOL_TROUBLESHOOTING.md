# P2Pool Troubleshooting Guide

## 🔍 Issue: P2Pool Shares Not Showing in Sentinel

If you found a share but it's not appearing in Sentinel, follow this checklist:

---

## ✅ Step 1: Verify Your Share Exists

Run the diagnostic tool:

```bash
python3 diagnose_p2pool.py YOUR_MONERO_ADDRESS --network main
```

This will show:
- ✅ If your address is valid
- ✅ If the P2Pool API can see your shares
- ✅ How many shares you have
- ✅ When your last share was found
- ✅ Current pool statistics

**Expected Output if Working:**
```
📋 Test 2: Miner Info API
  Status Code: 200
  ✅ Successfully retrieved miner info
  📊 Shares Array Length: 2
  Index 0 (Window): {'shares': 1, 'uncles': 0}
  Index 1 (Total): {'shares': 1, 'uncles': 0}

📋 Test 3: Recent Shares API
  ✅ Found 1 share(s)
  📄 Recent Shares:
    1. Height: 12345 | Time: 2024-01-30T10:30:00Z | Uncle: False
```

**If No Shares Found:**
- Wrong network? Try `--network mini` or `--network nano`
- Wrong address? Double-check your wallet address
- Share too old? Check the timestamp

---

## ✅ Step 2: Run Probe with P2Pool Address

Make sure you're running the probe WITH the P2Pool address:

```bash
python3 probe.py --host 127.0.0.1 \
  --p2pool-miner-address YOUR_MONERO_ADDRESS \
  --p2pool-network main
```

**What to Look For:**

The probe should output:
```
Fetching P2Pool stats for main network...
Miner address: YOUR_MONERO_ADDRESS
  Querying: https://p2pool.observer/api/miner_info/YOUR_ADDRESS
  Shares data array length: 2
  Shares in window (index 0): 1
  Total shares (index 1): 1
  Current pool height: 123456
  Found 1 total share(s) for this miner
    ✓ Share at height 123450 is in window
  ✅ Active shares in window: 1
  ✅ Total all-time shares: 1

  ✅ P2Pool stats stored successfully
  📊 Summary:
     Active in Window: 1
     Total Shares: 1
```

**If You Don't See This:**
- The address parameter wasn't passed
- There was a network error
- Check the error messages

---

## ✅ Step 3: Check Database

Verify the stats were stored:

```bash
python3 probe.py --stats
```

**Expected Output:**
```
=== Database Statistics ===
Total Miners: 2
Online Miners: 2
History Records: 150
P2Pool Miners: 1        ← This should be 1 or more
===========================
```

Or query directly:

```bash
python3 -c "
from database import SentinelDB
db = SentinelDB()
stats = db.get_all_p2pool_stats()
print(f'Found {len(stats)} P2Pool miner(s)')
for s in stats:
    print(f'  Address: {s[\"miner_address\"][:20]}...')
    print(f'  Active Shares: {s[\"active_shares\"]}')
    print(f'  Total Shares: {s[\"total_shares\"]}')
"
```

---

## ✅ Step 4: Check Dashboard

Open the dashboard:

```bash
streamlit run app.py
```

Navigate to http://localhost:8501

You should see a "🏊 P2Pool Stats" section with your stats.

**If Section is Empty:**
- Check "No P2Pool stats found" message
- Database might not have the data
- Try refreshing the page

---

## 🐛 Common Issues

### Issue 1: Wrong Network

**Symptom:** No shares found even though you know you have one

**Solution:**
```bash
# Try all networks
python3 diagnose_p2pool.py YOUR_ADDRESS --network main
python3 diagnose_p2pool.py YOUR_ADDRESS --network mini
python3 diagnose_p2pool.py YOUR_ADDRESS --network nano
```

P2Pool has three separate networks. Make sure you're checking the right one!

---

### Issue 2: Address Not Passed to Probe

**Symptom:** Miner stats show, but no P2Pool section

**Problem:** You're running:
```bash
python3 probe.py --host 127.0.0.1  ❌ Missing P2Pool address
```

**Solution:**
```bash
python3 probe.py --host 127.0.0.1 \
  --p2pool-miner-address YOUR_ADDRESS  ✅ Include this!
```

---

### Issue 3: Systemd Service Missing Address

**Symptom:** Manual run works, but systemd doesn't show P2Pool stats

**Problem:** Service file doesn't include the address

**Solution:** Edit `/etc/systemd/system/sentinel-probe.service`:

```ini
[Service]
ExecStart=/usr/bin/python3 probe.py --host 127.0.0.1 \
  --p2pool-miner-address YOUR_MONERO_ADDRESS \
  --p2pool-network main
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl restart sentinel-probe.timer
```

---

### Issue 4: Share Too Recent

**Symptom:** Share was found seconds/minutes ago but doesn't show

**Problem:** P2Pool observer API may have a delay (typically 1-5 minutes)

**Solution:** Wait a few minutes and run probe again:
```bash
# Wait 2-3 minutes
python3 probe.py --host 127.0.0.1 --p2pool-miner-address YOUR_ADDRESS
```

---

### Issue 5: Share Outside PPLNS Window

**Symptom:** Old share doesn't show in "Active Shares"

**Explanation:** P2Pool uses a PPLNS (Pay Per Last N Shares) window of 2160 blocks.

If your share is older than 2160 blocks ago, it won't be in the "Active" count, but WILL be in "Total Shares".

**Check:**
- Active Shares: Only recent shares (last ~24-48 hours)
- Total Shares: All shares ever found

---

## 📊 Understanding the Stats

### What Each Field Means:

**Active Shares (Window):**
- Shares found in the last 2160 blocks
- Used for PPLNS payout calculation
- Resets as blocks age out

**Total Shares:**
- All valid shares ever found
- Never decreases
- Historical record

**Active Uncles:**
- "Uncle" blocks in current window
- Side chain shares that didn't make main chain
- Still count for partial reward

**Payouts:**
- Currently shows "N/A"
- Future feature to track actual payouts

---

## 🔧 Force Refresh P2Pool Stats

If you think the data is stale:

```bash
# Run probe immediately
python3 probe.py --host 127.0.0.1 \
  --p2pool-miner-address YOUR_ADDRESS

# Check database
python3 probe.py --stats

# View in dashboard (it auto-refreshes every 30s)
streamlit run app.py
```

---

## 📝 Manual Database Check

If all else fails, check the database directly:

```bash
sqlite3 sentinel.db "SELECT * FROM p2pool_stats;"
```

**Example Output:**
```
YOUR_ADDRESS|2024-01-30 10:35:00|N/A|1|N/A|1|0|1|2024-01-30 09:00:00
```

Fields: miner_address | last_seen | blocks_found | shares_held | payouts_sent | active_shares | active_uncles | total_shares | created_at

---

## 🚀 Quick Diagnosis Commands

Run these in order:

```bash
# 1. Check if share exists on P2Pool
python3 diagnose_p2pool.py YOUR_ADDRESS --network main

# 2. Run probe with full output
python3 probe.py --host 127.0.0.1 \
  --p2pool-miner-address YOUR_ADDRESS \
  --p2pool-network main

# 3. Check database stats
python3 probe.py --stats

# 4. Check P2Pool entries in database
python3 -c "from database import SentinelDB; db = SentinelDB(); print(db.get_all_p2pool_stats())"

# 5. View in dashboard
streamlit run app.py
```

---

## 💡 Still Not Working?

1. **Check probe output** - It's very verbose now. Look for error messages.

2. **Try different networks:**
   ```bash
   --p2pool-network mini
   --p2pool-network nano
   ```

3. **Verify address format:**
   - Should be 95 characters (standard) or 106 (integrated)
   - Should start with '4' for mainnet

4. **Check API directly:**
   ```bash
   curl "https://p2pool.observer/api/miner_info/YOUR_ADDRESS"
   ```

5. **Wait for API delay** - Sometimes P2Pool observer takes 2-5 minutes to update

---

## 📞 Getting Help

If you're still stuck, provide:

1. Output of diagnostic tool:
   ```bash
   python3 diagnose_p2pool.py YOUR_ADDRESS --network main > p2pool_diag.txt
   ```

2. Output of probe run:
   ```bash
   python3 probe.py --host 127.0.0.1 \
     --p2pool-miner-address YOUR_ADDRESS 2>&1 | tee probe_output.txt
   ```

3. Database stats:
   ```bash
   python3 probe.py --stats
   ```

This will help identify exactly where the issue is!
