# Edge History Finder

**Two powerful tools for Microsoft Edge browser history:**

1. **History Search** - Find lost URLs by time window with smart exclusion filters
2. **Closed Tabs Finder** - Recover groups of tabs that were closed together

```
┌────────────────────────────────────────────┐
│  Edge History Finder                       │
│  ✓ Time window + exclusion filters         │
│  ✓ Tab group recovery via clustering       │
│  → Find that lost URL or restore tab groups│
└────────────────────────────────────────────┘
```

## Why This Exists

**Problem**: You closed a tab or tab group and can't remember the exact URL or site name.

**Solution**: 
- **History Search**: Remember it was around **12:00–19:00**? Exclude common sites (`google.com`, `youtube.com`) to narrow down to the interesting URLs.
- **Closed Tabs Finder**: Recover entire tab groups by detecting clusters of URLs visited within seconds of each other.

## Features

### History Search Tab
- Multiple Edge profiles support (**Default**, **Profile 1**, **Profile 2**, …)
- Date range + time window filtering (e.g., 12:00–19:00)
- **Typed-only toggle** - Show only URLs you actually typed (Chromium `urls.typed_count > 0`)
- **Negative filters** - Exclude domains/patterns (e.g., `google.com`, `youtube.com`)
- **Weekday filter** - Search only specific days of the week
- Results table with:
  - Local timestamp
  - Domain extraction
  - **Google Query** extraction for `google.*/search?q=...`
  - Full title and URL
- **Context menu** on results:
  - Copy selected URL(s)
  - Exclude selected domains
  - Exclude URL prefixes
- Settings persistence (filters, profile, time window)
- Auto-refresh on filter changes (debounced 250ms)

### Closed Tabs Finder Tab
- **Collapsible tab groups** with URL counts
- **Configurable clustering**:
  - Minimum URLs per group (default: 10)
  - Time window in seconds (default: 60)
- **URL deduplication** (on by default) with `{deduped}/{total}` counts
- **Sorting options**: Date/Time (default) or Alphabetical
- Auto-refresh when settings change

## Privacy & Safety

- ✅ **100% local** - Runs entirely on your machine
- ✅ **No network calls** - Never sends data anywhere
- ✅ **Read-only** - Copies Edge `History` SQLite DB to temp file (Edge locks the original)
- ✅ **No tracking** - No telemetry, analytics, or logging

## Installation

### Option 1: Run from source (Development)
```powershell
# Windows (Python 3.10+)
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m edge_history_finder
```

### Option 2: Build portable Windows EXE
```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
.\build.ps1
# Output: dist\EdgeHistoryFinder.exe
```

## Usage

### Finding a Lost URL
1. Switch to **History** tab
2. Set date range and time window
3. Add exclusions (e.g., `google.com`, `youtube.com`)
4. Optionally enable **Typed only** to filter URLs you directly typed
5. Optionally filter by weekday
6. Browse results - auto-refreshes as you adjust filters
7. Right-click to copy URLs or add more exclusions

### Recovering Closed Tab Groups
1. Switch to **Closed Tabs Finder** tab
2. Adjust date range (default: last 60 days)
3. Fine-tune clustering:
   - **Min URLs**: Minimum tabs to form a group (default: 10)
   - **Window (sec)**: Max seconds between tabs (default: 60)
4. Toggle **Deduplicate URLs** to remove duplicates
5. Choose sorting: **Date/Time** or **Alphabetical**
6. Click groups to expand/collapse URLs

## Bug Reports & Feature Requests

Found a bug or have a feature idea? [Open an issue on GitHub](https://github.com/tradmangh/edge-history-finder/issues/new/choose).

## Credits

**System design and intent**: Thomas Radman  
**Code generation**: OpenClaw & opencode using OpenAI GPT 5.2 Codex & Anthropic Sonnet 4.5

## License

**Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)**

- ✅ **Share** - Copy and redistribute
- ✅ **Adapt** - Remix, transform, and build upon the material
- ❌ **No Commercial Use** - Not for commercial purposes
- ⚠️ **Attribution Required** - Must credit the original source
- ⚠️ **ShareAlike** - Derivatives must use the same license

See [LICENSE](./LICENSE) for full terms.

## Technical Details

- **Language**: Python 3.10+
- **GUI Framework**: PySide6 (Qt)
- **Database**: Edge/Chromium SQLite History DB
- **Packaging**: PyInstaller for Windows EXE
- **Architecture**: Single-file modular structure (`app.py` + `history.py`)

## Keywords

Edge history, Chromium History SQLite, typed URLs, negative filter, exclude domains, find lost URL, google search query, tab group recovery, closed tabs finder, browser history search
