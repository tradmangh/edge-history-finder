# Tab Groups Finder - Design

**Date:** 2026-02-13
**Feature:** Find lost closed tab groups from Edge history
**Status:** Draft

## Overview

Add a "Find Tab Groups" feature that scans Edge history for URL clusters that likely represent restored tab groups. When users restore closed tabs, multiple URLs often open within a short time window. By detecting these clusters, we can help users find groups of URLs that were historically restored together.

## UI Specification

### Layout

**New Section** (below Search button, above Results table):
- Row with two QDateEdit: "From" / "To" (default: today → today-60 days)
- "Find Tab Groups" button (QPushButton)
- Results area below (QScrollArea with QVBoxLayout)

### Results Display

Each cluster displayed as a collapsible group:
- **Header**: Timestamp + "X URLs" count
- **Body**: List of URLs (QLabel or QListWidget)
- Sorted by timestamp (newest first)
- No filtering — pure display only

### Settings

- Store date range in QSettings under `tabGroupsFrom` / `tabGroupsTo`

## Functionality Specification

### Algorithm

```python
def find_tab_groups(history_db, start_dt, end_dt, min_urls=10, window_seconds=60):
    # 1. Query all visits in date range (ignore typed_only, excludes)
    # 2. Sort by visit_time ASC
    # 3. Sliding window: collect URLs within 60s of each other
    # 4. When gap > 60s: finalize current cluster
    # 5. Keep clusters with >10 URLs
    # 6. Sort clusters by timestamp DESC
```

### Data Structures

```python
@dataclass
class TabGroup:
    timestamp: str      # Formatted datetime
    urls: List[str]    # List of URLs in cluster
```

### New Functions (history.py)

- `find_tab_groups(history_db, start_dt, end_dt, min_urls=10, window_seconds=60) -> List[TabGroup]`

### New UI Methods (app.py)

- `on_find_tab_groups()` - handler for button click
- `_build_tab_groups_ui()` - builds the new section

## Default Values

- Date range: past 60 days
- Min URLs per cluster: >10
- Time window: 60 seconds

## Acceptance Criteria

1. User can select date range (default 60 days)
2. Clicking "Find Tab Groups" queries history and displays clusters
3. Each cluster shows timestamp and list of URLs
4. Only clusters with >10 URLs are shown
5. Results sorted by timestamp (newest first)
6. No filtering of results (display only)
7. Date range persists in settings
