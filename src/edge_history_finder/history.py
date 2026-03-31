from __future__ import annotations

import json
import os
import re
import shutil
import sqlite3
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class HistoryRow:
    local_time: str
    url: str
    title: str
    typed_count: int


@dataclass
class TabGroup:
    timestamp: str
    urls: list[str]


@dataclass
class DownloadRow:
    start_time: str  # formatted local datetime
    filename: str  # basename of target_path
    url: str  # source URL
    referrer_domain: str  # netloc of source URL
    total_bytes: int  # 0 if unknown
    state: int  # 0=in_progress 1=complete 2=cancelled 3=interrupted


@dataclass
class DomainStat:
    domain: str
    visits: int
    typed: int
    last_visit: str


@dataclass
class BookmarkEntry:
    title: str
    url: str
    added: str  # formatted datetime
    folder: str  # full folder path, e.g. "Bookmarks Bar › Work"


@dataclass
class PrivacySetting:
    label: str
    key_path: str  # dot-notation path in Preferences JSON
    value: object  # raw JSON value, or None if absent
    safe_when_false: bool | None  # True = off is private; None = neutral
    description: str


# ---------------------------------------------------------------------------
# Privacy checks catalogue
# ---------------------------------------------------------------------------

_PRIVACY_CHECKS: list[tuple[str, str, bool | None, str]] = [
    (
        "edge.history_screenshot.enabled",
        "Page snapshot history",
        True,
        "Edge captures page screenshots to display thumbnails in History",
    ),
    (
        "search.suggest_enabled",
        "Search suggestions",
        True,
        "Sends keystrokes to Microsoft as you type in the address bar",
    ),
    (
        "edge.autosuggestion_enabled",
        "Inline URL suggestions",
        True,
        "Sends URL fragments to Microsoft for address bar completions",
    ),
    (
        "metrics.reporting_enabled",
        "Crash & usage reporting",
        True,
        "Sends crash reports and usage statistics to Microsoft",
    ),
    (
        "autofill.credit_card_enabled",
        "Credit card autofill",
        None,
        "Saves and fills payment methods on sites",
    ),
    (
        "payments.can_make_payment_enabled",
        "Payment request API",
        True,
        "Allows sites to query whether you have saved payment methods",
    ),
    (
        "signin.allowed",
        "Browser sign-in / sync",
        None,
        "Allows signing into Edge and syncing data with your Microsoft account",
    ),
    (
        "profile.password_manager_enabled",
        "Built-in password manager",
        None,
        "Saves and fills passwords in the browser",
    ),
    (
        "edge.shopping_assistant_enabled",
        "Shopping assistant",
        True,
        "Sends product page URLs to Microsoft for price comparisons and coupons",
    ),
    (
        "edge.send_intranet_to_ie_enabled",
        "Send intranet to IE mode",
        None,
        "Automatically opens intranet sites in Internet Explorer mode",
    ),
]


# ---------------------------------------------------------------------------
# Profile / path helpers
# ---------------------------------------------------------------------------


def windows_edge_user_data_dir() -> Path | None:
    """Return the Edge User Data directory, or None if not found."""
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        return None
    p = Path(local) / "Microsoft" / "Edge" / "User Data"
    return p if p.exists() else None


def list_profiles(user_data_dir: Path) -> list[str]:
    """Scan for Edge profile dirs that contain a History file.

    Scans the directory rather than iterating a hardcoded range, so profiles
    beyond 'Profile 29' are discovered automatically.
    """
    out: list[str] = []
    try:
        for candidate in user_data_dir.iterdir():
            if not candidate.is_dir():
                continue
            if candidate.name == "Default" or re.fullmatch(
                r"Profile \d+", candidate.name
            ):
                if (candidate / "History").exists():
                    out.append(candidate.name)
    except OSError:
        return []

    def _sort_key(name: str) -> tuple[int, int]:
        if name == "Default":
            return (0, 0)
        m = re.fullmatch(r"Profile (\d+)", name)
        return (1, int(m.group(1))) if m else (2, 0)

    out.sort(key=_sort_key)
    return out


# ---------------------------------------------------------------------------
# Chrome epoch helpers
# ---------------------------------------------------------------------------


def chrome_time_to_unix_seconds(chrome_us: int) -> float:
    """Convert a Chrome/Edge microsecond timestamp (epoch 1601-01-01 UTC) to Unix seconds."""
    return (chrome_us / 1_000_000) - 11644473600


def unix_seconds_to_chrome_time(unix_seconds: float) -> int:
    return int((unix_seconds + 11644473600) * 1_000_000)


def dt_to_chrome_time(d: datetime) -> int:
    """Convert a (possibly naive, local-time) datetime to a Chrome microsecond timestamp."""
    if d.tzinfo is None:
        local_tz = datetime.now().astimezone().tzinfo
        d = d.replace(tzinfo=local_tz)
    return unix_seconds_to_chrome_time(d.timestamp())


# ---------------------------------------------------------------------------
# Temp DB helpers
# ---------------------------------------------------------------------------


def _copy_history_db(src: Path) -> Path:
    """Copy the History DB to a private temp dir to avoid SQLite lock contention.

    Cleans up the temp dir automatically if the copy fails.
    """
    tmp_dir = Path(tempfile.mkdtemp(prefix="edge-history-finder-"))
    dst = tmp_dir / "History.sqlite"
    try:
        shutil.copy2(src, dst)
    except Exception:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise
    return dst


def _remove_temp_db(db: Path) -> None:
    """Delete the temp directory created by _copy_history_db."""
    shutil.rmtree(db.parent, ignore_errors=True)


# ---------------------------------------------------------------------------
# History query
# ---------------------------------------------------------------------------


def query_history(
    history_db: Path,
    start_dt: datetime,
    end_dt: datetime,
    excludes: list[str],
    limit: int = 5000,
    typed_only: bool = True,
    weekdays: list[int] | None = None,
) -> list[HistoryRow]:
    excludes = list(excludes)  # materialise once — caller may pass any iterable
    db = _copy_history_db(history_db)

    start_ct = dt_to_chrome_time(start_dt)
    end_ct = dt_to_chrome_time(end_dt)

    exclude_sql = "".join([" AND urls.url NOT LIKE ?" for _ in excludes])
    typed_sql = " AND COALESCE(urls.typed_count, 0) > 0" if typed_only else ""

    weekday_sql = ""
    weekday_params: list[str] = []
    if weekdays:
        # SQLite strftime('%w'): 0=Sun..6=Sat
        weekday_sql = (
            " AND strftime('%w', datetime(visits.visit_time/1000000-11644473600,'unixepoch','localtime')) IN ("
            + ",".join(["?"] * len(weekdays))
            + ")"
        )
        weekday_params = [str(int(w)) for w in weekdays]

    params: list = (
        [start_ct, end_ct] + [f"%{x}%" for x in excludes] + weekday_params + [limit]
    )

    sql = f"""
    SELECT
      datetime(visits.visit_time/1000000-11644473600,'unixepoch','localtime') AS local_time,
      urls.url AS url,
      COALESCE(urls.title, '') AS title,
      COALESCE(urls.typed_count, 0) AS typed_count
    FROM urls
    JOIN visits ON visits.url = urls.id
    WHERE visits.visit_time BETWEEN ? AND ?
      {typed_sql}
      {exclude_sql}
      {weekday_sql}
    ORDER BY visits.visit_time ASC
    LIMIT ?;
    """

    con = sqlite3.connect(str(db))
    try:
        cur = con.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
    finally:
        con.close()
        _remove_temp_db(db)

    return [
        HistoryRow(str(local_time), str(url), str(title), int(typed_count))
        for local_time, url, title, typed_count in rows
    ]


# ---------------------------------------------------------------------------
# Tab groups (Closed Tabs Finder)
# ---------------------------------------------------------------------------


def find_tab_groups(
    history_db: Path,
    start_dt: datetime,
    end_dt: datetime,
    min_urls: int = 10,
    window_seconds: int = 60,
) -> list[TabGroup]:
    """Find clusters of URLs that were likely restored together as a tab group."""
    db = _copy_history_db(history_db)

    start_ct = dt_to_chrome_time(start_dt)
    end_ct = dt_to_chrome_time(end_dt)

    # LIMIT guards against huge date ranges causing UI freezes.
    sql = """
    SELECT
      visits.visit_time AS visit_time,
      urls.url AS url
    FROM urls
    JOIN visits ON visits.url = urls.id
    WHERE visits.visit_time BETWEEN ? AND ?
    ORDER BY visits.visit_time ASC
    LIMIT 100000;
    """

    con = sqlite3.connect(str(db))
    try:
        cur = con.cursor()
        cur.execute(sql, (start_ct, end_ct))
        rows = cur.fetchall()
    finally:
        con.close()
        _remove_temp_db(db)

    if not rows:
        return []

    # Sliding-window clustering on raw microsecond visit_time integers —
    # avoids per-row datetime parsing overhead.
    clusters: list[list[tuple[int, str]]] = []
    current_cluster: list[tuple[int, str]] = []
    window_us = window_seconds * 1_000_000

    for visit_time, url in rows:
        vt = int(visit_time)
        if not current_cluster:
            current_cluster.append((vt, str(url)))
            continue

        if vt - current_cluster[-1][0] <= window_us:
            current_cluster.append((vt, str(url)))
        else:
            if len(current_cluster) >= min_urls:
                clusters.append(current_cluster)
            current_cluster = [(vt, str(url))]

    if len(current_cluster) >= min_urls:
        clusters.append(current_cluster)

    result: list[TabGroup] = []
    for cluster in clusters:
        unix_s = chrome_time_to_unix_seconds(cluster[0][0])
        ts = datetime.fromtimestamp(unix_s).strftime("%Y-%m-%d %H:%M:%S")
        result.append(TabGroup(timestamp=ts, urls=[url for _, url in cluster]))

    result.sort(key=lambda g: g.timestamp, reverse=True)
    return result


# ---------------------------------------------------------------------------
# Downloads
# ---------------------------------------------------------------------------


def query_downloads(
    history_db: Path,
    start_dt: datetime,
    end_dt: datetime,
    limit: int = 2000,
) -> list[DownloadRow]:
    """Query the downloads table for entries in the given datetime range."""
    db = _copy_history_db(history_db)

    start_ct = dt_to_chrome_time(start_dt)
    end_ct = dt_to_chrome_time(end_dt)

    sql = """
    SELECT
      datetime(start_time/1000000-11644473600,'unixepoch','localtime') AS ts,
      COALESCE(target_path, current_path, '') AS path,
      COALESCE(tab_url, site_url, referrer, '') AS src_url,
      COALESCE(total_bytes, received_bytes, 0) AS bytes,
      COALESCE(state, 0) AS st
    FROM downloads
    WHERE start_time BETWEEN ? AND ?
      AND start_time > 0
    ORDER BY start_time DESC
    LIMIT ?;
    """

    con = sqlite3.connect(str(db))
    try:
        cur = con.cursor()
        try:
            cur.execute(sql, (start_ct, end_ct, limit))
            rows = cur.fetchall()
        except sqlite3.OperationalError:
            rows = []  # downloads table absent in some profiles
    finally:
        con.close()
        _remove_temp_db(db)

    result: list[DownloadRow] = []
    for ts, path, src_url, bytes_, state in rows:
        filename = Path(str(path)).name if path else ""
        domain = ""
        try:
            domain = urlparse(str(src_url)).netloc
        except Exception:
            pass
        result.append(
            DownloadRow(
                start_time=str(ts or ""),
                filename=filename,
                url=str(src_url or ""),
                referrer_domain=domain,
                total_bytes=int(bytes_ or 0),
                state=int(state or 0),
            )
        )
    return result


# ---------------------------------------------------------------------------
# Domain statistics
# ---------------------------------------------------------------------------


def query_domain_stats(
    history_db: Path,
    start_dt: datetime,
    end_dt: datetime,
    top_n: int = 150,
) -> list[DomainStat]:
    """Return top domains by visit count within the given date range."""
    db = _copy_history_db(history_db)

    start_ct = dt_to_chrome_time(start_dt)
    end_ct = dt_to_chrome_time(end_dt)

    # Fetch per-URL counts; aggregate by domain in Python (SQLite has no URL parser).
    sql = """
    SELECT
      urls.url,
      COUNT(visits.id) AS cnt,
      COALESCE(MAX(urls.typed_count), 0) AS typed,
      MAX(datetime(visits.visit_time/1000000-11644473600,'unixepoch','localtime')) AS last
    FROM urls
    JOIN visits ON visits.url = urls.id
    WHERE visits.visit_time BETWEEN ? AND ?
    GROUP BY urls.id
    ORDER BY cnt DESC
    LIMIT 20000;
    """

    con = sqlite3.connect(str(db))
    try:
        cur = con.cursor()
        cur.execute(sql, (start_ct, end_ct))
        rows = cur.fetchall()
    finally:
        con.close()
        _remove_temp_db(db)

    # Aggregate by domain
    domain_data: dict[str, list] = {}  # domain -> [visits, typed, last_visit]
    for url, cnt, typed, last in rows:
        try:
            domain = urlparse(str(url)).netloc or str(url)
        except Exception:
            domain = str(url)
        if domain not in domain_data:
            domain_data[domain] = [0, 0, ""]
        domain_data[domain][0] += int(cnt or 0)
        domain_data[domain][1] += int(typed or 0)
        if str(last or "") > domain_data[domain][2]:
            domain_data[domain][2] = str(last or "")

    result = [
        DomainStat(domain=d, visits=v[0], typed=v[1], last_visit=v[2])
        for d, v in domain_data.items()
    ]
    result.sort(key=lambda s: s.visits, reverse=True)
    return result[:top_n]


# ---------------------------------------------------------------------------
# Activity heatmap
# ---------------------------------------------------------------------------


def query_visit_heatmap(
    history_db: Path,
    days: int = 365,
) -> dict[str, int]:
    """Return a mapping of ISO date string → visit count for the last N days."""
    db = _copy_history_db(history_db)

    cutoff_dt = datetime.now() - timedelta(days=days)
    cutoff_ct = dt_to_chrome_time(cutoff_dt)

    sql = """
    SELECT
      date(datetime(visit_time/1000000-11644473600,'unixepoch','localtime')) AS d,
      COUNT(*) AS cnt
    FROM visits
    WHERE visit_time >= ?
    GROUP BY d;
    """

    con = sqlite3.connect(str(db))
    try:
        cur = con.cursor()
        cur.execute(sql, (cutoff_ct,))
        rows = cur.fetchall()
    finally:
        con.close()
        _remove_temp_db(db)

    return {str(d): int(cnt) for d, cnt in rows if d}


# ---------------------------------------------------------------------------
# Bookmarks
# ---------------------------------------------------------------------------


def _flatten_bookmarks(node: dict, path: str, out: list[BookmarkEntry]) -> None:
    ntype = node.get("type", "")
    name = str(node.get("name", ""))
    if ntype == "url":
        added_raw = int(node.get("date_added", 0))
        if added_raw:
            unix_s = chrome_time_to_unix_seconds(added_raw)
            try:
                added_str = datetime.fromtimestamp(unix_s).strftime("%Y-%m-%d %H:%M")
            except (OSError, OverflowError, ValueError):
                added_str = ""
        else:
            added_str = ""
        out.append(
            BookmarkEntry(
                title=name,
                url=str(node.get("url", "")),
                added=added_str,
                folder=path,
            )
        )
    elif ntype == "folder":
        sub_path = (f"{path} › {name}").lstrip(" › ")
        for child in node.get("children", []):
            _flatten_bookmarks(child, sub_path, out)


def read_bookmarks(bookmarks_path: Path) -> list[BookmarkEntry]:
    """Read and flatten the Edge Bookmarks JSON file into a list."""
    try:
        with open(bookmarks_path, encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []

    out: list[BookmarkEntry] = []
    for root_node in data.get("roots", {}).values():
        if isinstance(root_node, dict) and root_node.get("type") == "folder":
            for child in root_node.get("children", []):
                _flatten_bookmarks(child, "", out)
    return out


# ---------------------------------------------------------------------------
# Privacy settings
# ---------------------------------------------------------------------------


def _get_nested(d: dict, path: str) -> object:
    """Traverse a nested dict via dot-notation path. Returns None if absent."""
    node: object = d
    for part in path.split("."):
        if not isinstance(node, dict):
            return None
        node = node.get(part)
        if node is None:
            return None
    return node


def read_privacy_settings(preferences_path: Path) -> list[PrivacySetting]:
    """Read privacy-relevant settings from Edge's Preferences JSON file."""
    try:
        with open(preferences_path, encoding="utf-8") as f:
            prefs = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []

    return [
        PrivacySetting(
            label=label,
            key_path=key_path,
            value=_get_nested(prefs, key_path),
            safe_when_false=safe_when_false,
            description=description,
        )
        for key_path, label, safe_when_false, description in _PRIVACY_CHECKS
    ]
