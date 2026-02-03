# P2Pool Payout Tracking

## 🎉 What's New

Sentinel now tracks P2Pool payouts and blocks found!

## 📊 What Gets Tracked

### **1. Payouts Received**
- **Total number** of payouts received
- Displayed prominently in dashboard
- Updated every time probe runs

### **2. Blocks Found**
- Number of blocks found by your miner
- Shown in P2Pool stats section
- Rare but exciting when it happens! 🎉

### **3. Enhanced Display**
- Green success message when you have payouts
- Block count shown separately
- "No payouts yet" message when starting out

## 🔍 How It Works

### **API Queries**

When you run the probe with `--p2pool-miner-address`, Sentinel now queries:

1. **Miner Info** - Your shares
2. **Shares API** - Recent shares for verification
3. **Payouts API** - All payouts received ← **NEW!**
4. **Blocks API** - Blocks found by you ← **NEW!**

### **Example Output**

```bash
$ python3 probe.py --host 127.0.0.1 --p2pool-miner-address YOUR_ADDRESS --p2pool-network nano

Fetching P2Pool stats for nano network...
  Querying: https://nano.p2pool.observer/api/miner_info/YOUR_ADDRESS
  Shares data array length: 2
  P2Pool reports shares in window: 3
  Total shares (all-time): 135
  
  Found 4 total share(s) for this miner
  Window range: 754842 to 757002
    ✓ Share at height 756905 is in window
    ✓ Share at height 756547 is in window
    ✓ Share at height 756297 is in window
    ✗ Share at height 751192 is outside window (too old)
  
  Blocks found by miner: 0
  
  Querying: https://nano.p2pool.observer/api/payouts?miner=YOUR_ADDRESS
  Total payouts received: 12
  Latest payout: 0.002456 XMR at 2026-02-01T15:23:45Z
  Total paid out: 0.029472 XMR
  
  ✅ Active shares in window: 3
  ✅ Total all-time shares: 135
  ✅ P2Pool stats stored successfully
```

## 🎯 Dashboard Display

### **Before (Old):**
```
Active Shares: 3
Total Shares: 135
Active Uncles: 0
Payouts: N/A  ← Always showed N/A!
```

### **After (New):**
```
Active Shares: 3
Total Shares: 135
Active Uncles: 0
Blocks Found: 0

━━━━━━━━━━━━━━━━━━━━━━━━━
💰 Total Payouts Received: 12  ← Now shows actual count!
```

## 🧪 Testing Your Payouts

### **1. Diagnose Script**

The diagnostic script now tests payouts too:

```bash
python3 diagnose_p2pool.py YOUR_ADDRESS --network nano
```

**New Output:**
```
📋 Test 6: Payouts
  URL: https://nano.p2pool.observer/api/payouts?miner=YOUR_ADDRESS
  ✅ Found 12 payout(s)
  
  💰 Recent Payouts:
    1. Amount: 0.00245600 XMR | Time: 2026-02-01T15:23:45Z | Height: 756800
    2. Amount: 0.00241200 XMR | Time: 2026-02-01T08:15:30Z | Height: 756450
    3. Amount: 0.00238900 XMR | Time: 2026-01-31T22:47:12Z | Height: 756120
    ... and 9 more
  
  💎 Total Paid: 0.02947200 XMR
```

### **2. Run Probe**

Your regular probe run will now capture payouts:

```bash
python3 probe.py --host 127.0.0.1 \
  --p2pool-miner-address YOUR_ADDRESS \
  --p2pool-network nano
```

### **3. Check Dashboard**

Open your dashboard and navigate to the P2Pool Stats section:

```
http://localhost:8501
```

You'll now see your payout count!

## 📈 Understanding Payouts

### **When Do Payouts Happen?**

On P2Pool, you receive a payout **every time a block is found** by the network (not just you), as long as you have **active shares in the PPLNS window**.

- **Main/Mini**: More frequent payouts (higher network hashrate)
- **Nano**: Less frequent but still regular

### **Payout Amount**

Your payout is proportional to:
- Number of your active shares
- Total shares in the PPLNS window
- Block reward

```
Your Payout = (Your Active Shares / Total Window Shares) × Block Reward
```

### **Why Did I Get a Payout Yesterday But It Doesn't Show?**

If you got a payout yesterday but Sentinel shows 0:

1. **Make sure you're running probe with your address:**
   ```bash
   # Check your service/timer configuration
   cat /etc/systemd/system/sentinel-probe.service
   ```
   
   Should include:
   ```
   --p2pool-miner-address YOUR_ADDRESS
   ```

2. **Check the correct network:**
   ```bash
   # Are you mining on mini but checking main?
   --p2pool-network nano  # or main, or mini
   ```

3. **Test the API directly:**
   ```bash
   curl "https://nano.p2pool.observer/api/payouts?miner=YOUR_ADDRESS"
   ```

4. **Run the diagnostic:**
   ```bash
   python3 diagnose_p2pool.py YOUR_ADDRESS --network nano
   ```

## 🔄 Updating Your Installation

If you already have Sentinel installed:

1. **Update the files:**
   ```bash
   cd ~/sentinel
   cp /path/to/new/probe.py .
   cp /path/to/new/app.py .
   cp /path/to/new/diagnose_p2pool.py .
   ```

2. **Restart services:**
   ```bash
   sudo systemctl restart sentinel-probe.timer
   sudo systemctl restart sentinel-dash.service
   ```

3. **Test:**
   ```bash
   python3 probe.py --host 127.0.0.1 \
     --p2pool-miner-address YOUR_ADDRESS \
     --p2pool-network YOUR_NETWORK
   ```

## 📊 Database Structure

Payouts are stored in the `p2pool_stats` table:

```sql
SELECT 
  miner_address,
  payouts_sent,
  blocks_found,
  active_shares,
  total_shares
FROM p2pool_stats;
```

**Example:**
```
YOUR_ADDRESS | 12 | 0 | 3 | 135
```

## 🎁 Bonus: Blocks Found

If you're lucky enough to find a block, it will show up separately:

```
Blocks Found: 1  🎉
```

This is rare but possible, especially on smaller networks like nano!

## 💡 Pro Tips

1. **Check payouts regularly** to verify your setup is working
2. **Compare to your wallet** to ensure all payouts are tracked
3. **Use diagnose script** when troubleshooting
4. **Monitor active shares** - more shares = more frequent payouts

## 🐛 Troubleshooting

### **Payouts still show N/A**

- Update to latest version of `probe.py` and `app.py`
- Restart services
- Check probe is running with `--p2pool-miner-address`

### **Payouts show 0 but I received one**

- Check you're monitoring the correct network
- Verify address matches exactly
- Test with diagnostic script
- Check P2Pool observer API is responding

### **"Could not get payouts data" error**

- API may be temporarily unavailable
- Network connectivity issue
- Try again in a few minutes
- Check network selection (main/mini/nano)

## 📞 Support

If payouts still aren't tracking after trying these steps:

1. Run diagnostic and save output:
   ```bash
   python3 diagnose_p2pool.py YOUR_ADDRESS --network nano > payout_debug.txt
   ```

2. Check your probe logs:
   ```bash
   journalctl -u sentinel-probe.service -n 50
   ```

3. Report issue with both outputs

---

**Now go check your payouts!** 💰
