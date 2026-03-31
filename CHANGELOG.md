# Changelog

All notable changes to **Edge History Finder** are documented here.

Format: [CalVer](https://calver.org/) `vYYYY.MM.#` — newest first.

---

## [Unreleased] — v2026.03.1

> Pending tag `v2026.03.1` and CI release build.

### Bug fixes

- **`excludes` iterable consumed twice** — `query_history` materialises the
  argument to a `list` immediately, so generators and other single-pass iterables
  work correctly (previously the second iteration yielded nothing and no URLs
  were filtered out).
- **Temp-dir leak on DB copy failure** — `_copy_history_db` now removes the
  directory it created if `shutil.copy2` raises (e.g. permission denied, disk
  full). Previously the empty temp dir was left behind.
- **Weekday labels were German for all locales** — Checkboxes showed `Di`, `Mi`,
  `Do`, `So`, etc. even in English. All seven labels are now localised via the
  `tr()` / `_T` system (`Mon`/`Mo`, `Tue`/`Di`, `Wed`/`Mi`, …).
- **Google query extraction limited to `.com` and `.at`** — The
  *Google Query* column now recognises any Google TLD (`google.com`,
  `google.de`, `google.co.uk`, `google.fr`, …) via a domain-name check
  instead of two hard-coded `endswith` tests.
- **Off-by-one in tab-group cluster finalisation** — Changed `> min_urls` to
  `>= min_urls` at both cluster-close points in `find_tab_groups`, so clusters
  of exactly `min_urls` entries are no longer silently dropped.

### Improvements

- **`list_profiles` no longer limited to 29 profiles** — Profile discovery now
  scans the Edge User Data directory with `iterdir()` + regex instead of
  iterating a hard-coded `range(1, 30)`, so `Profile 30` and beyond are found
  automatically.
- **`_user_data_dir` cached at startup** — `windows_edge_user_data_dir()` was
  called on every search; it is now resolved once in `__init__` and stored as
  `self._user_data_dir`.
- **`Ctrl+C` copies selected rows** — `QShortcut(QKeySequence.StandardKey.Copy)`
  added to the results table; previously only double-click and right-click
  copied URLs.
- **Table batch rendering** — History results table wraps the row-fill loop in
  `setUpdatesEnabled(False/True)`, eliminating per-row repaint overhead.
  Noticeable speedup for large result sets (≥ 1 000 rows).
- **`QFont.Weight.Bold` replaces deprecated `QFont.Bold`** — Eliminates a Qt
  deprecation warning emitted for each Closed Tabs Finder group header.
- **Sort-mode constant** — `self.tgSortBy.currentIndex() == 1` replaced by
  `self.tgSortBy.currentIndex() == _SORT_ALPHA` (named module-level constant).
- **Help / About menu uses `tr()`** — Two strings that previously hard-coded
  `"Hilfe" if _LANG == "de" else "Help"` are now full i18n keys (`help_menu`,
  `about_action`) with EN and DE translations.
- **Tab-group context menu** — Right-click any URL in the Closed Tabs Finder
  tree to copy it to the clipboard.
- **Temp DB cleanup made reliable** — Both `query_history` and
  `find_tab_groups` wrap the connection in `try/finally` so the temp copy is
  always deleted even if the query raises.
- **`LIMIT 100000`** added to the tab-groups SQL query to prevent UI freezes on
  very wide date ranges.
- **`_remove_temp_db` simplified** — Removed a redundant `try/except` wrapper;
  `shutil.rmtree(ignore_errors=True)` alone suppresses errors.

### Code quality

- **Dead code removed**: `Settings` dataclass (never instantiated),
  `on_sel_changed` (never connected), `_current_url` (never called).
- **`self._last_result_count` initialised in `__init__`** — Previously
  bootstrapped lazily via `getattr(self, "_last_result_count", 0)`.
- **Stale comment removed** — `# status bar (initialized earlier)` was a
  leftover from an earlier refactor.
- **Type annotations modernised** — `Optional[X]` → `X | None`,
  `List[str]` → `list[str]`, `Iterable[str]` → `list[str]` throughout both
  modules. `from typing import …` imports removed entirely.
- **`from urllib.parse import parse_qs`** moved to top-level import (was
  inside the result-rendering loop body).
- **Unused imports removed** — `QPainter`, `QPixmap`, `QListWidgetItem`,
  `QMenuBar`, `QFrame`, `QScrollArea`, `datetime.timezone`.

### CI / versioning

- **CalVer `vYYYY.MM.#`** adopted; `pyproject.toml` version set to `2026.03.1`.
- **`release.yml` is tag-driven** — Trigger changed from `push → branches: main`
  to `push → tags: 'v[0-9][0-9][0-9][0-9].[0-9][0-9].*'`. The tag name is the
  single source of truth for the release version; a validation step fails CI if
  the tag and `pyproject.toml` diverge.
- **`.gitignore`** — Added `*.egg-info/` entry; removed stale
  `src/edge_history_finder.egg-info/` directory from the repository.

---

## [0.9.0] — 2026-02-17

> Commit `cd68785`

### Added

- **Closed Tabs Finder tab** — New second tab that clusters URLs visited within
  a configurable time window to detect tab groups that were closed together.
  - Collapsible tree widget; each group header shows timestamp and URL count.
  - **URL deduplication** toggle (on by default) with `deduped/total` counts.
  - **Sorting**: Date/Time (default) or Alphabetical.
  - Configurable **Min URLs** (default 10) and **Window (seconds)** (default 60).
  - Auto-refresh when any of the above settings change.
- **Auto-refresh on filter changes** (debounced 250 ms via `QTimer.singleShot`)
  across both tabs — removing the manual *Search* button as the primary
  interaction.
- **GitHub Actions release workflow** (`release.yml`) — Automated EXE build and
  GitHub Release on merge to `main`.
- Version `0.9.0` and GitHub link added to the About dialog.
- **License changed** from MIT to
  [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)
  (non-commercial).
- README rewritten for public release with installation, usage, and technical
  details sections.

---

## [0.8.x] — 2026-02-07 (afternoon / evening)

> Commits `4b7f79b` · `bc3fff3` · `3ca9eed`

### Added

- **Help menu** with **About dialog** — Version read from package metadata via
  `importlib.metadata`; falls back to `"dev"` when running from source.
- **"Don't show again" checkbox** in About dialog — choice persisted via
  `QSettings`.
- Splash screen replaced by a modal OK-dismiss dialog (the former timed splash
  was disruptive on slow machines).

---

## [0.7.x] — 2026-02-07 (afternoon)

> Commits `e9562f9` · `1f5d4d3` · `d000666` · `fae7e86`

### Added

- **Internationalisation (i18n)** — English and German UI via `_T` dict and
  `tr()` lookup; language detected from `QLocale.system()`. All visible strings
  translated.
- **Splash screen** — Shown on first launch; dismissed automatically.
- **GitHub issue templates** — Bug report and feature request templates
  (`.github/ISSUE_TEMPLATE/`).
- **Auto-refresh** on filter changes (debounced `QTimer`); dedicated *Search*
  button demoted to optional manual trigger.

### Fixed

- Crash on startup when `_load_settings()` ran before the status bar widget was
  created — status bar initialisation moved earlier in `__init__`.

---

## [0.6.x] — 2026-02-07 (early afternoon)

> Commits `a50539f` · `302ef94` · `4c51ae6` · `c439030`

### Added

- **Weekday filter** — Seven checkboxes (`Mon` – `Sun`) filter results to
  specific days via SQLite `strftime('%w', …)`. State persisted across sessions.
- **Settings persistence** — Profile index, time window, typed-only toggle,
  exclude list, and weekday selection all saved and restored via
  `QSettings("tradm", "EdgeHistoryFinder")` (Windows registry).
- **Domain column** — Extracted from each URL via `urlparse`.
- **Google Query column** — Extracts the `q=` parameter from
  `google.*/search` URLs so search terms are visible without opening the URL.
- **Typed-only toggle** — When enabled, restricts results to rows where
  `urls.typed_count > 0` (URLs the user directly typed rather than clicked).
- **Multi-select copy** — Selecting multiple rows and double-clicking or using
  the context menu copies all selected URLs, one per line.
- **Exclude context menu** — Right-click on the exclude list to remove entries
  or clear all.
- **Status bar** — Shows current profile, mode, exclude count, and result count.
- **Enter key** submits the exclude-add field.

---

## [0.5.x] — 2026-02-07 (morning)

> Commits `b7074e4` · `7d165bd` · `b4b8b85` · `d351802`

### Added

- **Double-click to copy URL** from results table.
- **Context menu on results** — Copy URL, exclude domain, exclude URL prefix.
- **PyInstaller build script** (`build.ps1`) producing a single-file
  `dist/EdgeHistoryFinder.exe` (`--onefile --windowed`).
- `PySide6 >= 6.8` version constraint pinned in `requirements.txt`.

### Fixed

- Chrome timestamp conversion on Windows when `datetime` is naive (no
  `timezone.localtime` call — broke on Windows where
  `datetime.timezone` is unavailable at import time).
- Running the app directly via `python -m src.edge_history_finder.app` now
  works alongside `python -m edge_history_finder`.

---

## [0.1.0] — 2026-02-07  *(Initial MVP)*

> Commit `3feaf27`

### Added

- **History Search** — Query Edge browser history by profile, date range, and
  time window.
- **Negative filters** — Exclude URLs containing specified patterns
  (e.g. `google.com`, `youtube.com`).
- Edge/Chromium SQLite `History` DB access via temp-copy to avoid lock
  contention while Edge is running.
- **Multi-profile support** (`Default`, `Profile 1` … `Profile N`).
- Chrome epoch conversion (`microseconds since 1601-01-01 UTC`).
- PySide6 GUI, `src/` layout packaging, `console_scripts` entry point
  (`edge-history-finder`).
- `.gitignore` for Python, venv, PyInstaller artefacts.
