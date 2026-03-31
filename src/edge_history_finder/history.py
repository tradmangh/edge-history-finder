from __future__ import annotations

import os
import re
import shutil
import sqlite3
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


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


def _copy_history_db(src: Path) -> Path:
    """Copy the History DB to a private temp dir to avoid SQLite lock contention.

    Cleans up the temp dir automatically if the copy fails, so callers never
    need to worry about leaked directories on error.
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
