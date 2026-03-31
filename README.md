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
- **Typed-only toggle** — Show only URLs you actually typed (Chromium `urls.typed_count > 0`)
- **Negative filters** — Exclude domains/patterns (e.g., `google.com`, `youtube.com`)
- **Weekday filter** — Search only specific days of the week
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
- **Context menu** on any URL — right-click to copy it directly
- Auto-refresh when settings change
- UI fully localised for English and German

## Privacy & Safety

- ✅ **100% local** — Runs entirely on your machine
- ✅ **No network calls** — Never sends data anywhere
- ✅ **Read-only** — Copies Edge `History` SQLite DB to a temp file (Edge locks the original); temp copy is deleted after each query
- ✅ **No tracking** — No telemetry, analytics, or logging

## Installation

### Option 1: Download portable EXE (recommended)

Grab the latest `EdgeHistoryFinder.exe` from the [Releases page](https://github.com/tradmangh/edge-history-finder/releases). No installation required — just run it.

### Option 2: Run from source

```powershell
# Windows, Python 3.10+
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m edge_history_finder
```

### Option 3: Build portable EXE yourself

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
.\build.ps1
# Output: dist\EdgeHistoryFinder.exe
```

## Usage

### Finding a Lost URL
1. Switch to the **History** tab
2. Set date range and time window
3. Add exclusions (e.g., `google.com`, `youtube.com`)
4. Optionally enable **Typed only** to filter URLs you directly typed
5. Optionally filter by weekday
6. Browse results — auto-refreshes as you adjust filters
7. Right-click any result to copy URLs or add more exclusions

### Recovering Closed Tab Groups
1. Switch to the **Closed Tabs Finder** tab
2. Adjust date range (default: last 60 days)
3. Fine-tune clustering:
   - **Min URLs** — Minimum tabs to form a group (default: 10)
   - **Window (sec)** — Max seconds between tabs in a cluster (default: 60)
4. Toggle **Deduplicate URLs** to remove duplicates within a group
5. Choose sorting: **Date/Time** or **Alphabetical**
6. Click a group header to expand/collapse its URLs
7. Right-click any URL to copy it

## Versioning

Releases follow **Calendar Versioning** (`vYYYY.MM.#`):

| Segment | Meaning | Example |
|---------|---------|---------|
| `YYYY` | Full year | `2026` |
| `MM` | Zero-padded month | `03` |
| `#` | Sequential build within the month (1-based) | `1` |

**Example**: `v2026.03.1` is the first release in March 2026. A second release that same month would be `v2026.03.2`.

To publish a release, create and push a tag that matches the version in `pyproject.toml`:
```powershell
git tag v2026.03.1
git push origin v2026.03.1
```
The CI workflow validates that the tag matches `pyproject.toml` and fails fast if they diverge.

## Bug Reports & Feature Requests

Found a bug or have a feature idea? [Open an issue on GitHub](https://github.com/tradmangh/edge-history-finder/issues/new/choose).

## Credits

**System design and intent**: Thomas Radman
**Code generation**: OpenClaw & opencode using OpenAI GPT 5.2 Codex & Anthropic Sonnet 4.5

## License

**Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)**

- ✅ **Share** — Copy and redistribute
- ✅ **Adapt** — Remix, transform, and build upon the material
- ❌ **No Commercial Use** — Not for commercial purposes
- ⚠️ **Attribution Required** — Must credit the original source
- ⚠️ **ShareAlike** — Derivatives must use the same license

See [LICENSE](./LICENSE) for full terms.

## Technical Details

- **Language**: Python 3.10+
- **GUI Framework**: PySide6 (Qt 6)
- **Database**: Edge/Chromium SQLite History DB (`%LOCALAPPDATA%\Microsoft\Edge\User Data\<Profile>\History`)
- **Packaging**: PyInstaller — single-file Windows EXE
- **Architecture**: `src/edge_history_finder/app.py` (GUI) + `history.py` (data layer)
- **Versioning**: CalVer `vYYYY.MM.#`

## Keywords

Edge history, Chromium History SQLite, typed URLs, negative filter, exclude domains, find lost URL, google search query, tab group recovery, closed tabs finder, browser history search
