# ThaiClub AutoBet APK v3.2

## Features
- JWT Token login OR Username+Password login (api.thaiclub1.us.cc)
- WinGo 30S / WinGo 1M support
- Mirror / Opposite / Random Opposite strategies
- Progressive betting: Martingale & Anti-Martingale
- Full timing control: trigger, pre-fetch, balance-check, settle delay
- Accurate P/L: per-round (new_balance - old_balance) AND session P/L
- Stop Profit / Stop Loss auto-stop
- Bet history table with round, issue, Daman, bet type, amount, result, P/L, balance
- Pause / Resume mid-session
- Live streak tracking (win streak, loss streak, best, worst)

## Build Options

### Option 1 — GitHub Actions (Easiest, free, no setup needed)
1. Create GitHub repo, push all files
2. Actions tab → workflow runs automatically
3. Download APK from Artifacts after ~20 min

### Option 2 — Linux (Ubuntu 20.04+)
```bash
chmod +x install_and_build.sh
./install_and_build.sh
```

### Option 3 — Google Colab
```python
!pip install buildozer Cython==0.29.33
!apt-get install -y openjdk-17-jdk zip unzip
!buildozer -v android debug
```
Then download `bin/*.apk`

## Install on Android
- Copy APK to phone → open → Allow unknown sources → Install
- OR: `adb install bin/*.apk`

## API Endpoints
- Login:   POST https://api.thaiclub1.us.cc/api/webapi/Login
- Balance: GET  https://api.01.versedkh.online/api/Lottery/GetBalance
- History: GET  https://draw.01.versedkh.online/WinGo/{gameCode}/GetHistoryIssuePage.json
- Bet:     POST https://api.01.versedkh.online/api/Lottery/WinGoBet

## Signature
MD5 of sorted JSON keys (uppercase hex), timestamp = Unix epoch seconds


## 30-Second Perfect Mode
- Default dual-round timing for 30s game: **26th second** and **57th second** each minute.
- Default dual pre-fetch timing: **20s** and **50s**.
- Default dual balance-check timing: **10s** and **40s**.
- All six timing points are editable in Settings.
