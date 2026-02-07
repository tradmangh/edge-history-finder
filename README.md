# Edge History Finder

Find lost URLs in your Microsoft Edge history when you only remember **rough time** and want to search by **exclusion**.

```
┌───────────────────────────────┐
│  Edge History Finder          │
│  time window + excludes       │
│  → narrow down to the odd URLs│
└───────────────────────────────┘
```

## Why this exists
Sometimes you don’t remember the site name, the day, or even whether it was a URL or a search. You *do* remember roughly **12:00–19:00** and you want to eliminate the usual suspects (`google.com`, `youtube.com`, …) until only the interesting URLs remain.

## Features
- Multiple Edge profiles (**Default**, **Profile 1**, **Profile 2**, …)
- Date range + time window filtering
- **Typed-only toggle** (Chromium `urls.typed_count > 0`) *or* show all visits
- Negative filter list (exclude domains / strings)
- Results table with:
  - **Domain** column
  - **Google Query** column for `google.* /search?q=...`
- Multi-select:
  - copy selected URL(s)
  - exclude selected domains / URL prefixes via context menu
- Weekday filter
- Settings persistence (filters, profile, time window)
- UI auto-refresh (debounced)

## Privacy & safety
- Runs locally.
- Reads Edge `History` SQLite DB by copying it to a temp file (Edge may lock the DB).
- No network calls.

## Install (dev)
```powershell
# Windows (recommended)
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m edge_history_finder
```

## Build a portable Windows EXE
```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
.\build.ps1
# output: dist\EdgeHistoryFinder.exe
```

## Credits
Written by **Thomas Radman**.
Co-authored by **OpenClaw / OpenAI Codex 5.2**.

## License
MIT — see [LICENSE](./LICENSE).

## Keywords
Edge history, Chromium History SQLite, typed URLs, negative filter, exclude domains, find lost URL, google search query.
