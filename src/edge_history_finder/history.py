from __future__ import annotations

import os
import shutil
import sqlite3
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional


@dataclass
class HistoryRow:
    local_time: str
    url: str
    title: str
    typed_count: int


def windows_edge_user_data_dir() -> Optional[Path]:
    # On Windows: %LOCALAPPDATA%\Microsoft\Edge\User Data
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        return None
    p = Path(local) / "Microsoft" / "Edge" / "User Data"
    return p if p.exists() else None


def list_profiles(user_data_dir: Path) -> List[str]:
    # Common profile dirs: Default, Profile 1, Profile 2, ...
    out: List[str] = []
    for name in ["Default"] + [f"Profile {i}" for i in range(1, 30)]:
        if (user_data_dir / name / "History").exists():
            out.append(name)
    return out


def chrome_time_to_unix_seconds(chrome_us: int) -> float:
    # Chrome/Edge: microseconds since 1601-01-01 UTC
    return (chrome_us / 1_000_000) - 11644473600


def unix_seconds_to_chrome_time(unix_seconds: float) -> int:
    return int((unix_seconds + 11644473600) * 1_000_000)


def dt_to_chrome_time(d: datetime) -> int:
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.localtime())  # best effort
    unix_s = d.timestamp()
    return unix_seconds_to_chrome_time(unix_s)


def _copy_history_db(src: Path) -> Path:
    # Copy to temp file to avoid locking issues.
    tmp_dir = Path(tempfile.mkdtemp(prefix="edge-history-finder-"))
    dst = tmp_dir / "History.sqlite"
    shutil.copy2(src, dst)
    return dst


def query_typed_urls(
    history_db: Path,
    start_dt: datetime,
    end_dt: datetime,
    excludes: Iterable[str],
    limit: int = 5000,
) -> List[HistoryRow]:
    db = _copy_history_db(history_db)

    start_ct = dt_to_chrome_time(start_dt)
    end_ct = dt_to_chrome_time(end_dt)

    exclude_sql = "".join([" AND urls.url NOT LIKE ?" for _ in excludes])
    params = [start_ct, end_ct] + [f"%{x}%" for x in excludes] + [limit]

    sql = f"""
    SELECT
      datetime(visits.visit_time/1000000-11644473600,'unixepoch','localtime') AS local_time,
      urls.url AS url,
      COALESCE(urls.title, '') AS title,
      COALESCE(urls.typed_count, 0) AS typed_count
    FROM urls
    JOIN visits ON visits.url = urls.id
    WHERE visits.visit_time BETWEEN ? AND ?
      AND COALESCE(urls.typed_count, 0) > 0
      {exclude_sql}
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

    out: List[HistoryRow] = []
    for (local_time, url, title, typed_count) in rows:
        out.append(HistoryRow(str(local_time), str(url), str(title), int(typed_count)))
    return out
