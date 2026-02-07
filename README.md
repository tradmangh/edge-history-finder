# edge-history-finder

Portable local tool to search Microsoft Edge browsing history by date/time range, profile, and negative filters (exclude domains/strings). Optimized for finding *typed URLs* when you don’t remember the site name.

## Features (MVP)
- Multiple Edge profiles (Default, Profile 1, Profile 2, …)
- Date range + time window filtering
- **Typed URLs only** (uses Chromium `urls.typed_count > 0`)
- Negative filter list (exclude `google.com`, `youtube.com`, …)
- Results table with copy-to-clipboard

## Privacy
- Runs locally.
- Reads Edge `History` SQLite DB in-place by copying it to a temp file (Edge may lock the DB).
- No network calls.

## Install (dev)
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux:   source .venv/bin/activate
pip install -r requirements.txt
python -m edge_history_finder
```

## Build portable (Windows EXE)
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
.\build.ps1
# output: dist\EdgeHistoryFinder.exe
```

---
Tom’s workflow: pick date range + time window, add exclude filters, copy the 1–2 URLs you’re hunting.
