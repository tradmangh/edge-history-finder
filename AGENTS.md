# PROJECT KNOWLEDGE BASE

**Generated:** 2026-02-13
**Commit:** 4b7f79b
**Branch:** main

## OVERVIEW

Windows desktop GUI (PySide6/Qt) to search Microsoft Edge browser history by date/time window, profile, weekday, and negative filters. Python 3.10+, no network, reads Chromium SQLite History DB via temp copy.

## STRUCTURE

```
edge-history-finder/
├── src/edge_history_finder/
│   ├── __main__.py       # CLI entry: `python -m edge_history_finder`
│   ├── app.py            # GUI (MainWindow, i18n, settings persistence, context menus) — 670 LOC
│   └── history.py        # Data layer: Edge profile discovery, Chrome-time conversion, SQL queries
├── build.ps1             # PyInstaller → dist/EdgeHistoryFinder.exe (Windows only)
├── pyproject.toml        # setuptools src-layout, console_script: edge-history-finder
├── requirements.txt      # PySide6 >=6.8, PyInstaller >=6.10
└── .github/ISSUE_TEMPLATE/
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add/change UI controls | `src/edge_history_finder/app.py` `MainWindow.__init__` | All widgets built inline in constructor |
| Change SQL query logic | `src/edge_history_finder/history.py` `query_history()` | Dynamic SQL with f-string params — parameterized via `?` |
| Add i18n strings | `src/edge_history_finder/app.py` `_T` dict | EN/DE only; `tr("key")` lookup |
| Modify Edge profile detection | `src/edge_history_finder/history.py` `list_profiles()` | Hardcoded scan of Default + Profile 1..29 |
| Change build output | `build.ps1` | PyInstaller --onefile --windowed |
| Settings persistence | `app.py` `_load_settings` / `_save_settings` | QSettings("tradm", "EdgeHistoryFinder") — Windows registry |

## CONVENTIONS

- **src-layout packaging**: all code under `src/`, pyproject.toml `package-dir = {"" = "src"}`
- **No type checker / linter / formatter configured** — no mypy, ruff, black, flake8
- **i18n via dict**: `_T` maps `{"en": {...}, "de": {...}}`; `tr(key)` resolves at runtime via `QLocale`
- **Dependencies in requirements.txt**, not pyproject.toml `[project.dependencies]`
- **Chrome time**: microseconds since 1601-01-01 UTC. Conversion in `history.py`
- **DB safety**: always copy History SQLite to tempdir before querying (Edge locks it)
- **Auto-refresh**: debounced 250ms via `QTimer.singleShot` on any filter change
- **Weekday mapping**: SQLite `strftime('%w')` → 0=Sun..6=Sat

## ANTI-PATTERNS (THIS PROJECT)

- `app.py` is a 670-line single-file GUI — no separation of concerns (no MVC/MVP)
- Inline widget construction in `__init__` — no `.ui` files or declarative layout
- `from urllib.parse import parse_qs` imported inside loop body (line 599) — should be top-level
- No tests, no CI, no linting

## COMMANDS

```bash
# Dev run
python -m edge_history_finder

# Install as CLI
pip install -e .
edge-history-finder

# Build portable EXE (Windows, venv activated)
pip install -r requirements.txt
.\build.ps1
# output: dist/EdgeHistoryFinder.exe
```

## NOTES

- **Windows-only**: `windows_edge_user_data_dir()` reads `%LOCALAPPDATA%\Microsoft\Edge\User Data`
- **No cross-platform support** — Edge path hardcoded to Windows
- QSettings stored in Windows registry under `HKCU\Software\tradm\EdgeHistoryFinder`
- Google query extraction only handles `google.com` and `google.at` — not other TLDs
- Profile scan hardcoded to max 29 profiles
- `query_history` limit defaults to 5000 rows
- Temp DB copies in `edge-history-finder-*` tempdir are never cleaned up
