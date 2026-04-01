# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import sys
from collections import Counter
from datetime import date, datetime, time, timedelta
from importlib.metadata import version as pkg_version
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from PySide6.QtCore import QDate, QLocale, QSettings, QTime, QTimer, Qt
from PySide6.QtGui import (
    QAction,
    QBrush,
    QColor,
    QFont,
    QGuiApplication,
    QKeySequence,
    QShortcut,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTimeEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .history import (
    find_tab_groups,
    list_profiles,
    query_domain_stats,
    query_downloads,
    query_history,
    query_visit_heatmap,
    read_bookmarks,
    read_privacy_settings,
    windows_edge_user_data_dir,
)

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

# Tab indices
_TAB_HISTORY = 0
_TAB_CLOSED = 1
_TAB_DOWNLOADS = 2
_TAB_ACTIVITY = 3
_TAB_STATS = 4
_TAB_PRIVACY = 5
_TAB_BOOKMARKS = 6

# tgSortBy combo indices — using constants avoids fragile currentIndex() == N checks
_SORT_DATETIME = 0
_SORT_ALPHA = 1

# Download state integer → i18n key
_DL_STATE_KEY: dict[int, str] = {
    0: "dl_in_progress",
    1: "dl_complete",
    2: "dl_cancelled",
    3: "dl_interrupted",
}


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _fmt_bytes(n: int) -> str:
    """Format byte count as a human-readable string."""
    if n <= 0:
        return "—"
    if n < 1_024:
        return f"{n} B"
    if n < 1_024**2:
        return f"{n / 1_024:.1f} KB"
    if n < 1_024**3:
        return f"{n / 1_024**2:.1f} MB"
    return f"{n / 1_024**3:.2f} GB"


def _heatmap_color(count: int, max_count: int) -> QColor:
    """Map a visit count to a GitHub-style green heatmap colour."""
    if count <= 0:
        return QColor(235, 237, 240)
    pct = count / max(max_count, 1)
    if pct < 0.25:
        return QColor(155, 233, 168)
    if pct < 0.5:
        return QColor(64, 196, 99)
    if pct < 0.75:
        return QColor(48, 161, 78)
    return QColor(33, 110, 57)


def _make_table(cols: list[str], stretch_col: int = -1) -> QTableWidget:
    """Create a standard read-only, sortable QTableWidget."""
    t = QTableWidget(0, len(cols))
    t.setHorizontalHeaderLabels(cols)
    t.setSelectionBehavior(QTableWidget.SelectRows)
    t.setSelectionMode(QTableWidget.ExtendedSelection)
    t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    t.setWordWrap(False)
    t.setSortingEnabled(True)
    hh = t.horizontalHeader()
    if stretch_col >= 0:
        hh.setSectionResizeMode(stretch_col, QHeaderView.ResizeMode.Stretch)
    return t


def _table_item(text: str, align: Qt.AlignmentFlag | None = None) -> QTableWidgetItem:
    item = QTableWidgetItem(text)
    if align:
        item.setTextAlignment(align)
    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
    return item


# ---------------------------------------------------------------------------
# Language / i18n
# ---------------------------------------------------------------------------


def _lang() -> str:
    try:
        lang = QLocale.system().language()
        if lang in (QLocale.German, QLocale.AustrianGerman, QLocale.SwissGerman):
            return "de"
    except Exception:
        pass
    return "en"


_LANG = _lang()

_T = {
    "en": {
        # General
        "title": "Edge History Finder",
        "ready": "Ready",
        "load": "Load",
        "scan": "Scan",
        "export_csv": "Export CSV",
        "export_html": "Export HTML",
        "export_saved": "Saved: {path}",
        "export_error": "Export failed",
        "filter_placeholder": "Filter results…",
        "no_data": "No data found",
        "dont_show_again": "Don't show again",
        # Controls
        "edge_user_data": "Edge User Data",
        "profile": "Profile",
        "date": "Date",
        "time": "Time",
        "from": "From",
        "to": "To",
        "limit": "Limit",
        "negative_filters": "Negative filters",
        "exclude_placeholder": "Exclude contains… (e.g. google.com)",
        "add": "Add",
        "weekdays": "Weekdays",
        "wd_mon": "Mon",
        "wd_tue": "Tue",
        "wd_wed": "Wed",
        "wd_thu": "Thu",
        "wd_fri": "Fri",
        "wd_sat": "Sat",
        "wd_sun": "Sun",
        "mode": "Mode",
        "typed_only": "Typed only",
        "search": "Search",
        "search_tip": "Optional: manual refresh (auto-refresh is enabled)",
        "copy_urls": "Copy selected URL(s)",
        "exclude_domains": "Exclude {n} domains",
        "exclude_domain": "Exclude domain",
        "exclude_prefixes": "Exclude {n} URL prefixes",
        "exclude_prefix": "Exclude this URL prefix",
        "copy_url": "Copy URL",
        "remove_selected": "Remove selected",
        "clear_all": "Clear all",
        "edge_not_found": "Edge not found",
        "edge_not_found_msg": "Could not find Edge user data directory via LOCALAPPDATA.",
        "history_not_found": "History not found",
        "invalid_range": "Invalid range",
        "invalid_range_msg": "End datetime is before start datetime.",
        "query_failed": "Query failed",
        # History tab
        "history": "History",
        "col_time": "Time",
        "col_domain": "Domain",
        "col_gq": "Google Query",
        "col_title": "Title",
        "col_url": "URL",
        # Closed Tabs tab
        "ClosedTabsFinder": "Closed Tabs",
        "tab_groups": "Tab Groups",
        "tab_groups_btn": "Find Tab Groups",
        "tab_groups_urls": "{n} URLs",
        "min_urls_label": "Min URLs:",
        "window_sec_label": "Window (sec):",
        "deduplicate": "Deduplicate URLs",
        "sort_by": "Sort by:",
        "sort_datetime": "Date/Time (default)",
        "sort_alpha": "Alphabetical",
        "no_tab_groups": "No tab groups found",
        "tab_groups_header": "Tab Groups (click to expand)",
        # Downloads tab
        "tab_downloads": "Downloads",
        "dl_col_date": "Date",
        "dl_col_file": "Filename",
        "dl_col_size": "Size",
        "dl_col_state": "State",
        "dl_col_domain": "Source Domain",
        "dl_col_url": "URL",
        "dl_complete": "Complete",
        "dl_cancelled": "Cancelled",
        "dl_interrupted": "Interrupted",
        "dl_in_progress": "In Progress",
        # Activity/Heatmap tab
        "tab_activity": "Activity",
        "hm_days_label": "Show last",
        "hm_days_suffix": " days",
        "hm_hint": "Click any cell to load that day's history in the History tab",
        "hm_less": "Less",
        "hm_more": "More",
        "hm_visits": "{n} visits",
        # Stats tab
        "tab_stats": "Stats",
        "st_col_rank": "#",
        "st_col_domain": "Domain",
        "st_col_visits": "Visits",
        "st_col_typed": "Typed",
        "st_col_last": "Last Visit",
        # Privacy tab
        "tab_privacy": "Privacy",
        "pv_col_setting": "Setting",
        "pv_col_status": "Status",
        "pv_col_value": "Current Value",
        "pv_col_desc": "Description",
        "pv_safe": "✅  Safe",
        "pv_warn": "⚠️  Active",
        "pv_neutral": "ℹ️  Info",
        "pv_unknown": "❓  Not found",
        "pv_prefs_not_found": "Preferences file not found for this profile.",
        "pv_note": (
            "Note: key paths may vary across Edge versions. "
            "'Not found' means the setting uses the browser default."
        ),
        # Bookmarks tab
        "tab_bookmarks": "Bookmarks",
        "bm_summary": "{total} bookmarks · {dups} duplicate URL(s)",
        "bm_no_dups": "No duplicate URLs found.",
        "bm_dup_section": "Duplicate URLs ({n})",
        "bm_all_section": "All Bookmarks ({n})",
        "bm_col_title": "Title",
        "bm_col_url": "URL",
        "bm_col_folder": "Folder",
        "bm_col_added": "Added",
        "bm_col_count": "Count",
        "bm_col_folders": "In Folders",
        "bm_not_found": "Bookmarks file not found for this profile.",
        # Help menu
        "help_menu": "Help",
        "about_action": "About",
    },
    "de": {
        # General
        "title": "Edge History Finder",
        "ready": "Bereit",
        "load": "Laden",
        "scan": "Scannen",
        "export_csv": "Als CSV exportieren",
        "export_html": "Als HTML exportieren",
        "export_saved": "Gespeichert: {path}",
        "export_error": "Export fehlgeschlagen",
        "filter_placeholder": "Ergebnisse filtern…",
        "no_data": "Keine Daten gefunden",
        "dont_show_again": "Nicht mehr anzeigen",
        # Controls
        "edge_user_data": "Edge-Benutzerdaten",
        "profile": "Profil",
        "date": "Datum",
        "time": "Uhrzeit",
        "from": "Von",
        "to": "Bis",
        "limit": "Limit",
        "negative_filters": "Negativfilter",
        "exclude_placeholder": "Ausschließen (enthält)… (z.B. google.com)",
        "add": "Hinzufügen",
        "weekdays": "Wochentage",
        "wd_mon": "Mo",
        "wd_tue": "Di",
        "wd_wed": "Mi",
        "wd_thu": "Do",
        "wd_fri": "Fr",
        "wd_sat": "Sa",
        "wd_sun": "So",
        "mode": "Modus",
        "typed_only": "Nur getippt",
        "search": "Suchen",
        "search_tip": "Optional: manuell aktualisieren (Auto-Refresh ist aktiv)",
        "copy_urls": "Ausgewählte URL(s) kopieren",
        "exclude_domains": "{n} Domains ausschließen",
        "exclude_domain": "Domain ausschließen",
        "exclude_prefixes": "{n} URL-Präfixe ausschließen",
        "exclude_prefix": "Dieses URL-Präfix ausschließen",
        "copy_url": "URL kopieren",
        "remove_selected": "Auswahl entfernen",
        "clear_all": "Alles löschen",
        "edge_not_found": "Edge nicht gefunden",
        "edge_not_found_msg": "Edge User Data wurde über LOCALAPPDATA nicht gefunden.",
        "history_not_found": "History nicht gefunden",
        "invalid_range": "Ungültiger Zeitraum",
        "invalid_range_msg": "Ende liegt vor Start.",
        "query_failed": "Abfrage fehlgeschlagen",
        # History tab
        "history": "Chronik",
        "col_time": "Zeit",
        "col_domain": "Domain",
        "col_gq": "Google-Suchbegriff",
        "col_title": "Titel",
        "col_url": "URL",
        # Closed Tabs tab
        "ClosedTabsFinder": "Geschlossene Tabs",
        "tab_groups": "Tab-Gruppen",
        "tab_groups_btn": "Tab-Gruppen finden",
        "tab_groups_urls": "{n} URLs",
        "min_urls_label": "Min. URLs:",
        "window_sec_label": "Fenster (Sek.):",
        "deduplicate": "URLs deduplizieren",
        "sort_by": "Sortieren nach:",
        "sort_datetime": "Datum/Uhrzeit (Standard)",
        "sort_alpha": "Alphabetisch",
        "no_tab_groups": "Keine Tab-Gruppen gefunden",
        "tab_groups_header": "Tab-Gruppen (klicken zum Aufklappen)",
        # Downloads tab
        "tab_downloads": "Downloads",
        "dl_col_date": "Datum",
        "dl_col_file": "Dateiname",
        "dl_col_size": "Größe",
        "dl_col_state": "Status",
        "dl_col_domain": "Quell-Domain",
        "dl_col_url": "URL",
        "dl_complete": "Abgeschlossen",
        "dl_cancelled": "Abgebrochen",
        "dl_interrupted": "Unterbrochen",
        "dl_in_progress": "In Bearbeitung",
        # Activity/Heatmap tab
        "tab_activity": "Aktivität",
        "hm_days_label": "Letzte",
        "hm_days_suffix": " Tage",
        "hm_hint": "Zelle anklicken, um den Verlauf dieses Tages im Chronik-Tab zu laden",
        "hm_less": "Weniger",
        "hm_more": "Mehr",
        "hm_visits": "{n} Besuche",
        # Stats tab
        "tab_stats": "Statistiken",
        "st_col_rank": "#",
        "st_col_domain": "Domain",
        "st_col_visits": "Besuche",
        "st_col_typed": "Getippt",
        "st_col_last": "Zuletzt besucht",
        # Privacy tab
        "tab_privacy": "Datenschutz",
        "pv_col_setting": "Einstellung",
        "pv_col_status": "Status",
        "pv_col_value": "Aktueller Wert",
        "pv_col_desc": "Beschreibung",
        "pv_safe": "✅  Sicher",
        "pv_warn": "⚠️  Aktiv",
        "pv_neutral": "ℹ️  Info",
        "pv_unknown": "❓  Nicht gefunden",
        "pv_prefs_not_found": "Preferences-Datei für dieses Profil nicht gefunden.",
        "pv_note": (
            "Hinweis: Schlüsselpfade können je nach Edge-Version variieren. "
            "'Nicht gefunden' bedeutet, dass der Browser-Standard gilt."
        ),
        # Bookmarks tab
        "tab_bookmarks": "Lesezeichen",
        "bm_summary": "{total} Lesezeichen · {dups} Duplikat(e)",
        "bm_no_dups": "Keine doppelten URLs gefunden.",
        "bm_dup_section": "Doppelte URLs ({n})",
        "bm_all_section": "Alle Lesezeichen ({n})",
        "bm_col_title": "Titel",
        "bm_col_url": "URL",
        "bm_col_folder": "Ordner",
        "bm_col_added": "Hinzugefügt",
        "bm_col_count": "Anzahl",
        "bm_col_folders": "In Ordnern",
        "bm_not_found": "Lesezeichen-Datei für dieses Profil nicht gefunden.",
        # Help menu
        "help_menu": "Hilfe",
        "about_action": "Info",
    },
}


def tr(key: str, **fmt) -> str:
    s = _T.get(_LANG, _T["en"]).get(key, _T["en"].get(key, key))
    try:
        return s.format(**fmt)
    except Exception:
        return s


# ---------------------------------------------------------------------------
# MainWindow
# ---------------------------------------------------------------------------


class MainWindow(QMainWindow):
    # ── Settings persistence ────────────────────────────────────────────────

    def _load_settings(self):
        s = self._qsettings

        ex = s.value("excludes", [], list)
        if isinstance(ex, str):
            ex = [ex]
        if ex:
            self.excludeList.clear()
            for v in ex:
                if v and str(v).strip():
                    self.excludeList.addItem(str(v).strip())

        to = s.value("typedOnly", True)
        if isinstance(to, str):
            to = to.lower() in ("1", "true", "yes")
        self.typedOnly.setChecked(bool(to))

        wd = s.value("weekdays", [0, 1, 2, 3, 4, 5, 6], list)
        if isinstance(wd, str):
            wd = [int(x) for x in wd.split(",") if x.strip().isdigit()]
        wd_set = set(int(x) for x in wd)
        self.wd_sun.setChecked(0 in wd_set)
        self.wd_mon.setChecked(1 in wd_set)
        self.wd_tue.setChecked(2 in wd_set)
        self.wd_wed.setChecked(3 in wd_set)
        self.wd_thu.setChecked(4 in wd_set)
        self.wd_fri.setChecked(5 in wd_set)
        self.wd_sat.setChecked(6 in wd_set)

        pi = s.value("profileIndex", 0)
        try:
            pi = int(pi)
        except Exception:
            pi = 0
        if 0 <= pi < self.profile.count():
            self.profile.setCurrentIndex(pi)

        for attr, key, default in [
            ("timeStart", "timeStart", "12:00"),
            ("timeEnd", "timeEnd", "19:00"),
        ]:
            val = s.value(key, default)
            try:
                hh, mm = [int(x) for x in str(val).split(":", 1)]
                getattr(self, attr).setTime(time(hh, mm))
            except Exception:
                pass

        lim = s.value("limit", 5000)
        try:
            self.limit.setValue(int(lim))
        except Exception:
            pass

    def _save_settings(self):
        s = self._qsettings
        s.setValue("excludes", self.excludes())
        s.setValue("typedOnly", bool(self.typedOnly.isChecked()))
        s.setValue("profileIndex", int(self.profile.currentIndex()))
        s.setValue("timeStart", self.timeStart.time().toString("HH:mm"))
        s.setValue("timeEnd", self.timeEnd.time().toString("HH:mm"))
        s.setValue("limit", int(self.limit.value()))
        wds: list[int] = []
        for bit, cb in enumerate(
            [
                self.wd_sun,
                self.wd_mon,
                self.wd_tue,
                self.wd_wed,
                self.wd_thu,
                self.wd_fri,
                self.wd_sat,
            ]
        ):
            if cb.isChecked():
                wds.append(bit)
        s.setValue("weekdays", wds)

    # ── Constructor ─────────────────────────────────────────────────────────

    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr("title"))
        self.resize(1200, 750)

        # Cached once at startup — avoids repeated filesystem hits on every query.
        self._user_data_dir: Path | None = windows_edge_user_data_dir()
        self._last_result_count: int = 0

        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)

        self._build_history_tab()
        self._build_closed_tabs_tab()
        self._build_downloads_tab()
        self._build_activity_tab()
        self._build_stats_tab()
        self._build_privacy_tab()
        self._build_bookmarks_tab()

        # ── Timers ──────────────────────────────────────────────────────────
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.timeout.connect(self.on_search)

        self._tg_refresh_timer = QTimer(self)
        self._tg_refresh_timer.setSingleShot(True)
        self._tg_refresh_timer.timeout.connect(self.on_find_tab_groups)

        # ── Global wiring ───────────────────────────────────────────────────
        self.tabs.currentChanged.connect(self._on_tab_changed)

        # ── Status bar ──────────────────────────────────────────────────────
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage(tr("ready"))

        # ── Persistent settings ─────────────────────────────────────────────
        self._qsettings = QSettings("tradm", "EdgeHistoryFinder")

        # ── Menu ────────────────────────────────────────────────────────────
        help_menu = self.menuBar().addMenu(tr("help_menu"))
        act_about = QAction(tr("about_action"), self)
        act_about.triggered.connect(lambda: _show_about_dialog(self, self._qsettings))
        help_menu.addAction(act_about)

        self._load_settings()
        self._update_status()

    # ── Tab builders ─────────────────────────────────────────────────────────

    def _build_history_tab(self) -> None:
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)

        controls = QWidget()
        form = QFormLayout(controls)
        tab_layout.addWidget(controls)

        self.profile = QComboBox()
        self.profilePath = QLineEdit()
        self.profilePath.setReadOnly(True)

        if self._user_data_dir is None:
            self.profilePath.setPlaceholderText(
                "Windows Edge User Data not found. Set path manually later."
            )
        else:
            self.profilePath.setText(str(self._user_data_dir))
            for p in list_profiles(self._user_data_dir):
                self.profile.addItem(p)

        self.profile.currentIndexChanged.connect(
            lambda _i: (
                self._update_status(),
                self._save_settings(),
                self._schedule_refresh(),
            )
        )

        self.dateStart = QDateEdit()
        self.dateStart.setCalendarPopup(True)
        self.dateStart.setDate(datetime.now().date())

        self.dateEnd = QDateEdit()
        self.dateEnd.setCalendarPopup(True)
        self.dateEnd.setDate(datetime.now().date())

        self.timeStart = QTimeEdit()
        self.timeStart.setTime(time(12, 0))
        self.timeEnd = QTimeEdit()
        self.timeEnd.setTime(time(19, 0))

        self.limit = QSpinBox()
        self.limit.setRange(1, 50000)
        self.limit.setValue(5000)

        self.dateStart.dateChanged.connect(lambda _d: self._schedule_refresh())
        self.dateEnd.dateChanged.connect(lambda _d: self._schedule_refresh())
        self.timeStart.timeChanged.connect(lambda _t: self._schedule_refresh())
        self.timeEnd.timeChanged.connect(lambda _t: self._schedule_refresh())
        self.limit.valueChanged.connect(lambda _v: self._schedule_refresh())

        form.addRow(tr("edge_user_data"), self.profilePath)
        form.addRow(tr("profile"), self.profile)

        row_dt = QWidget()
        row_dt_l = QHBoxLayout(row_dt)
        row_dt_l.setContentsMargins(0, 0, 0, 0)
        row_dt_l.addWidget(QLabel(tr("from")))
        row_dt_l.addWidget(self.dateStart)
        row_dt_l.addWidget(QLabel(tr("to")))
        row_dt_l.addWidget(self.dateEnd)
        row_dt_l.addStretch(1)
        form.addRow(tr("date"), row_dt)

        row_t = QWidget()
        row_t_l = QHBoxLayout(row_t)
        row_t_l.setContentsMargins(0, 0, 0, 0)
        row_t_l.addWidget(QLabel(tr("from")))
        row_t_l.addWidget(self.timeStart)
        row_t_l.addWidget(QLabel(tr("to")))
        row_t_l.addWidget(self.timeEnd)
        row_t_l.addStretch(1)
        form.addRow(tr("time"), row_t)

        form.addRow(tr("limit"), self.limit)

        self.typedOnly = QCheckBox(tr("typed_only"))
        self.typedOnly.setChecked(True)
        self.typedOnly.stateChanged.connect(
            lambda _s: (
                self._update_status(),
                self._save_settings(),
                self._schedule_refresh(),
            )
        )
        form.addRow(tr("mode"), self.typedOnly)

        # Weekday filter (SQLite %w: 0=Sun … 6=Sat)
        wd_row = QWidget()
        wd_l = QHBoxLayout(wd_row)
        wd_l.setContentsMargins(0, 0, 0, 0)
        self.wd_mon = QCheckBox(tr("wd_mon"))
        self.wd_tue = QCheckBox(tr("wd_tue"))
        self.wd_wed = QCheckBox(tr("wd_wed"))
        self.wd_thu = QCheckBox(tr("wd_thu"))
        self.wd_fri = QCheckBox(tr("wd_fri"))
        self.wd_sat = QCheckBox(tr("wd_sat"))
        self.wd_sun = QCheckBox(tr("wd_sun"))
        for cb in [
            self.wd_mon,
            self.wd_tue,
            self.wd_wed,
            self.wd_thu,
            self.wd_fri,
            self.wd_sat,
            self.wd_sun,
        ]:
            cb.setChecked(True)
            cb.stateChanged.connect(
                lambda _s: (self._save_settings(), self._schedule_refresh())
            )
            wd_l.addWidget(cb)
        wd_l.addStretch(1)
        form.addRow(tr("weekdays"), wd_row)

        # Excludes
        ex_wrap = QWidget()
        ex_l = QHBoxLayout(ex_wrap)
        ex_l.setContentsMargins(0, 0, 0, 0)
        self.excludeInput = QLineEdit()
        self.excludeInput.setPlaceholderText(tr("exclude_placeholder"))
        self.excludeAdd = QPushButton(tr("add"))
        self.excludeRemove = QPushButton(tr("remove_selected"))
        ex_l.addWidget(self.excludeInput)
        ex_l.addWidget(self.excludeAdd)
        ex_l.addWidget(self.excludeRemove)
        form.addRow(tr("negative_filters"), ex_wrap)

        self.excludeList = QListWidget()
        self.excludeList.setContextMenuPolicy(Qt.CustomContextMenu)
        self.excludeList.addItem("google.com")
        self.excludeList.addItem("youtube.com")
        self.excludeList.setMaximumHeight(70)
        tab_layout.addWidget(self.excludeList)

        # Search + inline filter row
        btn_row = QWidget()
        btn_l = QHBoxLayout(btn_row)
        btn_l.setContentsMargins(0, 0, 0, 0)
        self.searchBtn = QPushButton(tr("search"))
        self.searchBtn.setToolTip(tr("search_tip"))
        btn_l.addWidget(self.searchBtn)
        self.filterInput = QLineEdit()
        self.filterInput.setPlaceholderText(tr("filter_placeholder"))
        self.filterInput.setClearButtonEnabled(True)
        btn_l.addWidget(self.filterInput)
        self.exportCsvBtn = QPushButton(tr("export_csv"))
        self.exportHtmlBtn = QPushButton(tr("export_html"))
        btn_l.addWidget(self.exportCsvBtn)
        btn_l.addWidget(self.exportHtmlBtn)
        tab_layout.addWidget(btn_row)

        # Results table
        self.table = _make_table(
            [
                tr("col_time"),
                tr("col_domain"),
                tr("col_gq"),
                tr("col_title"),
                tr("col_url"),
            ],
            stretch_col=4,
        )
        self.table.setSortingEnabled(False)  # keep chronological order
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        tab_layout.addWidget(self.table, 1)

        # Ctrl+C copies selected URLs
        QShortcut(QKeySequence.StandardKey.Copy, self.table).activated.connect(
            self.on_copy
        )

        self.tabs.addTab(tab, tr("history"))

        # Wire history-tab signals
        self.excludeAdd.clicked.connect(self.on_add_exclude)
        self.excludeInput.returnPressed.connect(self.on_add_exclude)
        self.excludeRemove.clicked.connect(self.on_remove_exclude)
        self.excludeList.customContextMenuRequested.connect(
            self.on_exclude_context_menu
        )
        self.searchBtn.clicked.connect(self.on_search)
        self.filterInput.textChanged.connect(self._apply_inline_filter)
        self.exportCsvBtn.clicked.connect(
            lambda: self._export_table_csv(self.table, "edge_history.csv")
        )
        self.exportHtmlBtn.clicked.connect(self._export_history_html)
        self.table.itemDoubleClicked.connect(self.on_double_click)
        self.table.customContextMenuRequested.connect(self.on_table_context_menu)

    def _build_closed_tabs_tab(self) -> None:
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)

        tg_section = QWidget()
        tg_form = QFormLayout(tg_section)
        tg_form.setContentsMargins(0, 10, 0, 0)

        tg_row = QWidget()
        tg_row_l = QHBoxLayout(tg_row)
        tg_row_l.setContentsMargins(0, 0, 0, 0)

        self.tgDateStart = QDateEdit()
        self.tgDateStart.setCalendarPopup(True)
        self.tgDateEnd = QDateEdit()
        self.tgDateEnd.setCalendarPopup(True)
        default_end = datetime.now().date()
        default_start = default_end - timedelta(days=60)
        self.tgDateStart.setDate(default_start)
        self.tgDateEnd.setDate(default_end)

        tg_row_l.addWidget(QLabel(tr("from")))
        tg_row_l.addWidget(self.tgDateStart)
        tg_row_l.addWidget(QLabel(tr("to")))
        tg_row_l.addWidget(self.tgDateEnd)

        tg_row_l.addWidget(QLabel("  " + tr("min_urls_label")))
        self.tgMinUrls = QSpinBox()
        self.tgMinUrls.setRange(1, 100)
        self.tgMinUrls.setValue(10)
        tg_row_l.addWidget(self.tgMinUrls)

        tg_row_l.addWidget(QLabel("  " + tr("window_sec_label")))
        self.tgWindowSeconds = QSpinBox()
        self.tgWindowSeconds.setRange(1, 600)
        self.tgWindowSeconds.setValue(60)
        tg_row_l.addWidget(self.tgWindowSeconds)
        tg_row_l.addStretch(1)

        tg_form.addRow(tr("tab_groups"), tg_row)

        tg_opts = QWidget()
        tg_opts_l = QHBoxLayout(tg_opts)
        tg_opts_l.setContentsMargins(0, 0, 0, 0)
        self.tgDeduplicate = QCheckBox(tr("deduplicate"))
        self.tgDeduplicate.setChecked(True)
        tg_opts_l.addWidget(self.tgDeduplicate)
        tg_opts_l.addWidget(QLabel("  " + tr("sort_by")))
        self.tgSortBy = QComboBox()
        self.tgSortBy.addItem(tr("sort_datetime"))
        self.tgSortBy.addItem(tr("sort_alpha"))
        tg_opts_l.addWidget(self.tgSortBy)
        tg_opts_l.addStretch(1)
        tg_form.addRow("", tg_opts)
        tab_layout.addWidget(tg_section)

        self.tgResults = QTreeWidget()
        self.tgResults.setHeaderLabels([tr("tab_groups_header")])
        self.tgResults.setAlternatingRowColors(True)
        self.tgResults.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tgResults.customContextMenuRequested.connect(self.on_tg_context_menu)
        tab_layout.addWidget(self.tgResults, 1)

        self.tabs.addTab(tab, tr("ClosedTabsFinder"))

        self.tgDateStart.dateChanged.connect(lambda _d: self._schedule_tg_refresh())
        self.tgDateEnd.dateChanged.connect(lambda _d: self._schedule_tg_refresh())
        self.tgMinUrls.valueChanged.connect(lambda _v: self._schedule_tg_refresh())
        self.tgWindowSeconds.valueChanged.connect(
            lambda _v: self._schedule_tg_refresh()
        )
        self.tgDeduplicate.stateChanged.connect(lambda _s: self._schedule_tg_refresh())
        self.tgSortBy.currentIndexChanged.connect(
            lambda _i: self._schedule_tg_refresh()
        )

    def _build_downloads_tab(self) -> None:
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)

        ctrl = QWidget()
        ctrl_l = QHBoxLayout(ctrl)
        ctrl_l.setContentsMargins(0, 0, 0, 0)

        ctrl_l.addWidget(QLabel(tr("from")))
        self.dlDateStart = QDateEdit()
        self.dlDateStart.setCalendarPopup(True)
        self.dlDateStart.setDate(datetime.now().date())
        ctrl_l.addWidget(self.dlDateStart)

        ctrl_l.addWidget(QLabel(tr("to")))
        self.dlDateEnd = QDateEdit()
        self.dlDateEnd.setCalendarPopup(True)
        self.dlDateEnd.setDate(datetime.now().date())
        ctrl_l.addWidget(self.dlDateEnd)

        ctrl_l.addWidget(QLabel(tr("limit")))
        self.dlLimit = QSpinBox()
        self.dlLimit.setRange(1, 10000)
        self.dlLimit.setValue(2000)
        ctrl_l.addWidget(self.dlLimit)

        self.dlLoadBtn = QPushButton(tr("load"))
        ctrl_l.addWidget(self.dlLoadBtn)

        self.dlFilterInput = QLineEdit()
        self.dlFilterInput.setPlaceholderText(tr("filter_placeholder"))
        self.dlFilterInput.setClearButtonEnabled(True)
        ctrl_l.addWidget(self.dlFilterInput)

        self.dlExportBtn = QPushButton(tr("export_csv"))
        ctrl_l.addWidget(self.dlExportBtn)
        ctrl_l.addStretch(1)
        tab_layout.addWidget(ctrl)

        self.dlTable = _make_table(
            [
                tr("dl_col_date"),
                tr("dl_col_file"),
                tr("dl_col_size"),
                tr("dl_col_state"),
                tr("dl_col_domain"),
                tr("dl_col_url"),
            ],
            stretch_col=5,
        )
        tab_layout.addWidget(self.dlTable, 1)

        self.tabs.addTab(tab, tr("tab_downloads"))

        self.dlLoadBtn.clicked.connect(self.on_load_downloads)
        self.dlFilterInput.textChanged.connect(
            lambda t: self._filter_table(self.dlTable, t)
        )
        self.dlExportBtn.clicked.connect(
            lambda: self._export_table_csv(self.dlTable, "edge_downloads.csv")
        )

    def _build_activity_tab(self) -> None:
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)

        # Controls
        ctrl = QWidget()
        ctrl_l = QHBoxLayout(ctrl)
        ctrl_l.setContentsMargins(0, 0, 0, 0)
        ctrl_l.addWidget(QLabel(tr("hm_days_label")))
        self.hmDays = QSpinBox()
        self.hmDays.setRange(30, 730)
        self.hmDays.setValue(365)
        self.hmDays.setSuffix(tr("hm_days_suffix"))
        ctrl_l.addWidget(self.hmDays)
        self.hmLoadBtn = QPushButton(tr("load"))
        ctrl_l.addWidget(self.hmLoadBtn)
        ctrl_l.addStretch(1)
        tab_layout.addWidget(ctrl)

        hint = QLabel(tr("hm_hint"))
        hint.setStyleSheet("color: #666; font-size: 11px; margin-bottom: 4px;")
        tab_layout.addWidget(hint)

        # Heatmap table — 7 rows (Mon–Sun), up to 54 columns (weeks)
        _CELL = 14
        self.hmTable = QTableWidget(7, 54)
        self.hmTable.setShowGrid(False)
        self.hmTable.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.hmTable.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.hmTable.horizontalHeader().setDefaultSectionSize(_CELL)
        self.hmTable.horizontalHeader().setMinimumSectionSize(_CELL)
        self.hmTable.verticalHeader().setDefaultSectionSize(_CELL)
        self.hmTable.verticalHeader().setMinimumSectionSize(_CELL)
        self.hmTable.verticalHeader().setMaximumWidth(28)
        self.hmTable.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        for i, label in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
            self.hmTable.setVerticalHeaderItem(i, QTableWidgetItem(label))
        heatmap_height = (
            self.hmTable.horizontalHeader().height()
            + (
                self.hmTable.rowCount()
                * self.hmTable.verticalHeader().defaultSectionSize()
            )
            + (self.hmTable.frameWidth() * 2)
            + 8
        )
        self.hmTable.setFixedHeight(heatmap_height)
        self.hmTable.cellClicked.connect(self._on_heatmap_click)
        tab_layout.addWidget(self.hmTable)

        # Legend
        legend = QWidget()
        legend_l = QHBoxLayout(legend)
        legend_l.setContentsMargins(30, 4, 0, 0)
        legend_l.addWidget(QLabel(tr("hm_less")))
        for cnt, mx in [(0, 15), (3, 15), (6, 15), (11, 15), (15, 15)]:
            swatch = QLabel()
            swatch.setFixedSize(12, 12)
            c = _heatmap_color(cnt, mx)
            swatch.setStyleSheet(f"background:{c.name()}; border:1px solid #ccc;")
            legend_l.addWidget(swatch)
        legend_l.addWidget(QLabel(tr("hm_more")))
        legend_l.addStretch(1)
        tab_layout.addWidget(legend)

        tab_layout.addStretch(1)

        self.tabs.addTab(tab, tr("tab_activity"))

        self.hmLoadBtn.clicked.connect(self.on_load_heatmap)

    def _build_stats_tab(self) -> None:
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)

        ctrl = QWidget()
        ctrl_l = QHBoxLayout(ctrl)
        ctrl_l.setContentsMargins(0, 0, 0, 0)
        ctrl_l.addWidget(QLabel(tr("from")))
        self.stDateStart = QDateEdit()
        self.stDateStart.setCalendarPopup(True)
        self.stDateStart.setDate(datetime.now().date() - timedelta(days=30))
        ctrl_l.addWidget(self.stDateStart)
        ctrl_l.addWidget(QLabel(tr("to")))
        self.stDateEnd = QDateEdit()
        self.stDateEnd.setCalendarPopup(True)
        self.stDateEnd.setDate(datetime.now().date())
        ctrl_l.addWidget(self.stDateEnd)
        self.stLoadBtn = QPushButton(tr("load"))
        ctrl_l.addWidget(self.stLoadBtn)
        self.stExportBtn = QPushButton(tr("export_csv"))
        ctrl_l.addWidget(self.stExportBtn)
        ctrl_l.addStretch(1)
        tab_layout.addWidget(ctrl)

        self.stTable = _make_table(
            [
                tr("st_col_rank"),
                tr("st_col_domain"),
                tr("st_col_visits"),
                tr("st_col_typed"),
                tr("st_col_last"),
            ],
            stretch_col=1,
        )
        tab_layout.addWidget(self.stTable, 1)

        self.tabs.addTab(tab, tr("tab_stats"))

        self.stLoadBtn.clicked.connect(self.on_load_stats)
        self.stExportBtn.clicked.connect(
            lambda: self._export_table_csv(self.stTable, "edge_stats.csv")
        )

    def _build_privacy_tab(self) -> None:
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)

        ctrl = QWidget()
        ctrl_l = QHBoxLayout(ctrl)
        ctrl_l.setContentsMargins(0, 0, 0, 0)
        self.pvScanBtn = QPushButton(tr("scan"))
        ctrl_l.addWidget(self.pvScanBtn)
        ctrl_l.addStretch(1)
        tab_layout.addWidget(ctrl)

        note = QLabel(tr("pv_note"))
        note.setWordWrap(True)
        note.setStyleSheet("color: #666; font-size: 11px; margin-bottom: 4px;")
        tab_layout.addWidget(note)

        self.pvTable = _make_table(
            [
                tr("pv_col_setting"),
                tr("pv_col_status"),
                tr("pv_col_value"),
                tr("pv_col_desc"),
            ],
            stretch_col=3,
        )
        self.pvTable.setColumnWidth(0, 200)
        self.pvTable.setColumnWidth(1, 90)
        self.pvTable.setColumnWidth(2, 100)
        tab_layout.addWidget(self.pvTable, 1)

        self.tabs.addTab(tab, tr("tab_privacy"))

        self.pvScanBtn.clicked.connect(self.on_scan_privacy)

    def _build_bookmarks_tab(self) -> None:
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)

        ctrl = QWidget()
        ctrl_l = QHBoxLayout(ctrl)
        ctrl_l.setContentsMargins(0, 0, 0, 0)
        self.bmScanBtn = QPushButton(tr("scan"))
        ctrl_l.addWidget(self.bmScanBtn)
        self.bmFilterInput = QLineEdit()
        self.bmFilterInput.setPlaceholderText(tr("filter_placeholder"))
        self.bmFilterInput.setClearButtonEnabled(True)
        ctrl_l.addWidget(self.bmFilterInput)
        self.bmExportBtn = QPushButton(tr("export_csv"))
        ctrl_l.addWidget(self.bmExportBtn)
        ctrl_l.addStretch(1)
        tab_layout.addWidget(ctrl)

        self.bmSummaryLabel = QLabel()
        self.bmSummaryLabel.setStyleSheet("font-weight: bold; margin: 4px 0;")
        tab_layout.addWidget(self.bmSummaryLabel)

        splitter = QSplitter(Qt.Orientation.Vertical)

        # Duplicates table
        dup_box = QGroupBox()
        self.bmDupBoxLabel = dup_box  # keep reference to update title
        dup_layout = QVBoxLayout(dup_box)
        dup_layout.setContentsMargins(4, 4, 4, 4)
        self.bmDupTable = _make_table(
            [tr("bm_col_url"), tr("bm_col_count"), tr("bm_col_folders")],
            stretch_col=0,
        )
        dup_layout.addWidget(self.bmDupTable)
        splitter.addWidget(dup_box)

        # All bookmarks table
        all_box = QGroupBox()
        self.bmAllBoxLabel = all_box
        all_layout = QVBoxLayout(all_box)
        all_layout.setContentsMargins(4, 4, 4, 4)
        self.bmAllTable = _make_table(
            [
                tr("bm_col_title"),
                tr("bm_col_url"),
                tr("bm_col_folder"),
                tr("bm_col_added"),
            ],
            stretch_col=1,
        )
        all_layout.addWidget(self.bmAllTable)
        splitter.addWidget(all_box)

        splitter.setSizes([180, 420])
        tab_layout.addWidget(splitter, 1)

        self.tabs.addTab(tab, tr("tab_bookmarks"))

        self.bmScanBtn.clicked.connect(self.on_scan_bookmarks)
        self.bmFilterInput.textChanged.connect(
            lambda t: self._filter_table(self.bmAllTable, t)
        )
        self.bmExportBtn.clicked.connect(
            lambda: self._export_table_csv(self.bmAllTable, "edge_bookmarks.csv")
        )

    # ── Helpers ──────────────────────────────────────────────────────────────

    def excludes(self) -> list[str]:
        return [
            self.excludeList.item(i).text().strip()
            for i in range(self.excludeList.count())
            if self.excludeList.item(i).text().strip()
        ]

    def _schedule_refresh(self):
        self._refresh_timer.start(250)

    def _schedule_tg_refresh(self):
        self._tg_refresh_timer.start(250)

    def _on_tab_changed(self, index: int):
        if index == _TAB_CLOSED:
            self.on_find_tab_groups()

    def _history_db(self) -> Path | None:
        """Return path to current profile's History DB, or None."""
        if self._user_data_dir is None:
            return None
        profile = self.profile.currentText() or "Default"
        p = self._user_data_dir / profile / "History"
        return p if p.exists() else None

    def _profile_dir(self) -> Path | None:
        """Return current profile directory path, or None."""
        if self._user_data_dir is None:
            return None
        profile = self.profile.currentText() or "Default"
        return self._user_data_dir / profile

    def _require_history_db(self, caller: str = "") -> Path | None:
        """Return history DB path, showing an error message if absent."""
        if self._user_data_dir is None:
            QMessageBox.warning(self, tr("edge_not_found"), tr("edge_not_found_msg"))
            return None
        p = self._history_db()
        if p is None:
            QMessageBox.warning(self, tr("history_not_found"), "History DB not found.")
            return None
        return p

    # ── Inline filter ─────────────────────────────────────────────────────────

    def _apply_inline_filter(self, text: str):
        """Filter the main history results table by multi-word text match."""
        self._filter_table(self.table, text)

    def _filter_table(self, table: QTableWidget, text: str):
        """Show/hide rows in *table* based on space-separated filter terms."""
        terms = text.strip().lower().split()
        for row in range(table.rowCount()):
            if not terms:
                table.setRowHidden(row, False)
                continue
            row_text = " ".join(
                (table.item(row, col) or QTableWidgetItem()).text()
                for col in range(table.columnCount())
            ).lower()
            table.setRowHidden(row, not all(t in row_text for t in terms))

    # ── Export helpers ────────────────────────────────────────────────────────

    def _export_table_csv(self, table: QTableWidget, default_name: str):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export CSV", default_name, "CSV (*.csv)"
        )
        if not path:
            return
        try:
            headers = [
                (
                    table.horizontalHeaderItem(c).text()
                    if table.horizontalHeaderItem(c)
                    else f"Col{c}"
                )
                for c in range(table.columnCount())
            ]
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(headers)
                for r in range(table.rowCount()):
                    if table.isRowHidden(r):
                        continue
                    w.writerow(
                        [
                            (table.item(r, c) or QTableWidgetItem()).text()
                            for c in range(table.columnCount())
                        ]
                    )
            self.status.showMessage(tr("export_saved", path=path))
        except Exception as e:
            QMessageBox.critical(self, tr("export_error"), str(e))

    def _export_history_html(self):
        """Export visible history results as a Netscape bookmarks HTML file."""
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Bookmarks HTML", "edge_history.html", "HTML (*.html)"
        )
        if not path:
            return
        try:
            lines = [
                "<!DOCTYPE NETSCAPE-Bookmark-file-1>",
                '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">',
                "<TITLE>Edge History Export</TITLE>",
                "<H1>Edge History Export</H1>",
                "<DL><p>",
            ]
            for r in range(self.table.rowCount()):
                if self.table.isRowHidden(r):
                    continue
                title = (self.table.item(r, 3) or QTableWidgetItem()).text()
                url = (self.table.item(r, 4) or QTableWidgetItem()).text()
                if url:
                    safe_title = (
                        title.replace("&", "&amp;")
                        .replace("<", "&lt;")
                        .replace(">", "&gt;")
                    )
                    lines.append(f'    <DT><A HREF="{url}">{safe_title or url}</A>')
            lines.append("</DL>")
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            self.status.showMessage(tr("export_saved", path=path))
        except Exception as e:
            QMessageBox.critical(self, tr("export_error"), str(e))

    # ── Exclude list ──────────────────────────────────────────────────────────

    def on_add_exclude(self):
        t = self.excludeInput.text().strip()
        if not t:
            return
        if t not in set(self.excludes()):
            self.excludeList.addItem(t)
        self.excludeInput.clear()
        self._update_status()
        self._save_settings()
        self._schedule_refresh()

    def on_remove_exclude(self):
        for it in self.excludeList.selectedItems():
            self.excludeList.takeItem(self.excludeList.row(it))
        self._update_status()
        self._save_settings()
        self._schedule_refresh()

    def on_exclude_context_menu(self, pos):
        items = self.excludeList.selectedItems()
        menu = QMenu(self)
        act_rm = QAction(tr("remove_selected"), self)
        act_rm.setEnabled(bool(items))
        act_rm.triggered.connect(self.on_remove_exclude)
        menu.addAction(act_rm)
        act_clear = QAction(tr("clear_all"), self)
        act_clear.setEnabled(self.excludeList.count() > 0)

        def _clear_all():
            self.excludeList.clear()
            self._update_status()
            self._save_settings()
            self._schedule_refresh()

        act_clear.triggered.connect(_clear_all)
        menu.addAction(act_clear)
        menu.exec(self.excludeList.viewport().mapToGlobal(pos))

    # ── Table helpers (History) ───────────────────────────────────────────────

    def _selected_urls(self) -> list[str]:
        rows = sorted({it.row() for it in self.table.selectedItems()})
        return [
            it.text().strip()
            for r in rows
            if (it := self.table.item(r, 4)) and it.text().strip()
        ]

    def on_copy(self):
        urls = self._selected_urls()
        if urls:
            QGuiApplication.clipboard().setText("\n".join(urls))

    def on_double_click(self, _item):
        self.on_copy()

    def _add_exclude_values(self, values: list[str]):
        for v in values:
            v = v.strip()
            if v and v not in set(self.excludes()):
                self.excludeList.addItem(v)

    def on_table_context_menu(self, pos):
        urls = self._selected_urls()
        if not urls:
            return
        menu = QMenu(self)

        act_copy = QAction(tr("copy_urls"), self)
        act_copy.triggered.connect(self.on_copy)
        menu.addAction(act_copy)

        hosts = sorted({urlparse(u).netloc for u in urls if urlparse(u).netloc})
        if hosts:
            label = (
                tr("exclude_domain")
                if len(hosts) == 1
                else tr("exclude_domains", n=len(hosts))
            )
            act_ex = QAction(label, self)
            act_ex.triggered.connect(lambda: self._add_exclude_values(hosts))
            menu.addAction(act_ex)

        prefixes = sorted(
            {
                f"{p.scheme}://{p.netloc}{p.path}"
                for u in urls
                if (p := urlparse(u)) and p.netloc
            }
        )
        if prefixes:
            label = (
                tr("exclude_prefix")
                if len(prefixes) == 1
                else tr("exclude_prefixes", n=len(prefixes))
            )
            act_ep = QAction(label, self)
            act_ep.triggered.connect(lambda: self._add_exclude_values(prefixes))
            menu.addAction(act_ep)

        menu.exec(self.table.viewport().mapToGlobal(pos))

    # ── Status bar ────────────────────────────────────────────────────────────

    def _update_status(self, result_count: int | None = None):
        typed = "typed-only" if self.typedOnly.isChecked() else "all-visits"
        if result_count is not None:
            self._last_result_count = result_count
        self.status.showMessage(
            f"Profile: {self.profile.currentText() or 'Default'}"
            f" | Mode: {typed}"
            f" | Excludes: {self.excludeList.count()}"
            f" | Results: {self._last_result_count}"
        )

    # ── History search ────────────────────────────────────────────────────────

    def on_search(self):
        history_db = self._require_history_db()
        if history_db is None:
            return

        start_dt = datetime.combine(
            self.dateStart.date().toPython(), self.timeStart.time().toPython()
        )
        end_dt = datetime.combine(
            self.dateEnd.date().toPython(), self.timeEnd.time().toPython()
        )
        if end_dt < start_dt:
            QMessageBox.warning(self, tr("invalid_range"), tr("invalid_range_msg"))
            return

        weekdays: list[int] = []
        for bit, cb in enumerate(
            [
                self.wd_sun,
                self.wd_mon,
                self.wd_tue,
                self.wd_wed,
                self.wd_thu,
                self.wd_fri,
                self.wd_sat,
            ]
        ):
            if cb.isChecked():
                weekdays.append(bit)

        try:
            rows = query_history(
                history_db=history_db,
                start_dt=start_dt,
                end_dt=end_dt,
                excludes=self.excludes(),
                limit=int(self.limit.value()),
                typed_only=bool(self.typedOnly.isChecked()),
                weekdays=weekdays,
            )
        except Exception as e:
            QMessageBox.critical(self, tr("query_failed"), str(e))
            return

        self.table.setUpdatesEnabled(False)
        try:
            self.table.setRowCount(0)
            for r in rows:
                row_i = self.table.rowCount()
                self.table.insertRow(row_i)
                self.table.setItem(row_i, 0, _table_item(r.local_time))

                domain = gq = ""
                try:
                    u = urlparse(r.url)
                    domain = u.netloc
                    if u.path.startswith("/search") and (
                        ".google." in u.netloc or u.netloc.startswith("google.")
                    ):
                        qv = parse_qs(u.query).get("q")
                        if qv:
                            gq = qv[0]
                except Exception:
                    pass

                self.table.setItem(row_i, 1, _table_item(domain))
                self.table.setItem(row_i, 2, _table_item(gq))
                self.table.setItem(row_i, 3, _table_item(r.title))
                self.table.setItem(row_i, 4, _table_item(r.url))
        finally:
            self.table.setUpdatesEnabled(True)

        if rows:
            self.table.selectRow(0)
        # Re-apply any active inline filter after reload
        self._apply_inline_filter(self.filterInput.text())
        self._update_status(result_count=len(rows))

    # ── Closed Tabs Finder ────────────────────────────────────────────────────

    def on_find_tab_groups(self):
        history_db = self._require_history_db()
        if history_db is None:
            return

        ds = self.tgDateStart.date().toPython()
        de = self.tgDateEnd.date().toPython()
        start_dt = datetime.combine(ds, datetime.min.time())
        end_dt = datetime.combine(de, datetime.max.time())
        if end_dt < start_dt:
            QMessageBox.warning(self, tr("invalid_range"), tr("invalid_range_msg"))
            return

        try:
            groups = find_tab_groups(
                history_db=history_db,
                start_dt=start_dt,
                end_dt=end_dt,
                min_urls=int(self.tgMinUrls.value()),
                window_seconds=int(self.tgWindowSeconds.value()),
            )
        except Exception as e:
            QMessageBox.critical(self, tr("query_failed"), str(e))
            return

        self.tgResults.clear()

        if not groups:
            self.tgResults.addTopLevelItem(QTreeWidgetItem([tr("no_tab_groups")]))
            return

        deduplicate = self.tgDeduplicate.isChecked()
        sort_alphabetically = self.tgSortBy.currentIndex() == _SORT_ALPHA

        for group in groups:
            urls = group.urls
            total_count = len(urls)
            if deduplicate:
                urls = list(dict.fromkeys(urls))
            if sort_alphabetically:
                urls = sorted(urls)

            if deduplicate:
                header_text = f"{group.timestamp} — {len(urls)}/{total_count} URLs"
            else:
                header_text = (
                    f"{group.timestamp} — {tr('tab_groups_urls', n=total_count)}"
                )

            parent_item = QTreeWidgetItem([header_text])
            parent_item.setFont(0, QFont("", -1, QFont.Weight.Bold))
            for url in urls:
                child = QTreeWidgetItem([url])
                child.setForeground(0, QColor("#0066cc"))
                parent_item.addChild(child)
            self.tgResults.addTopLevelItem(parent_item)
            parent_item.setExpanded(False)

    def on_tg_context_menu(self, pos):
        item = self.tgResults.itemAt(pos)
        if not item or item.parent() is None:
            return
        url = item.text(0).strip()
        if not url:
            return
        menu = QMenu(self)
        act_copy = QAction(tr("copy_url"), self)
        act_copy.triggered.connect(lambda: QGuiApplication.clipboard().setText(url))
        menu.addAction(act_copy)
        menu.exec(self.tgResults.viewport().mapToGlobal(pos))

    # ── Downloads ─────────────────────────────────────────────────────────────

    def on_load_downloads(self):
        history_db = self._require_history_db()
        if history_db is None:
            return

        start_dt = datetime.combine(
            self.dlDateStart.date().toPython(), datetime.min.time()
        )
        end_dt = datetime.combine(self.dlDateEnd.date().toPython(), datetime.max.time())
        if end_dt < start_dt:
            QMessageBox.warning(self, tr("invalid_range"), tr("invalid_range_msg"))
            return

        try:
            rows = query_downloads(
                history_db=history_db,
                start_dt=start_dt,
                end_dt=end_dt,
                limit=int(self.dlLimit.value()),
            )
        except Exception as e:
            QMessageBox.critical(self, tr("query_failed"), str(e))
            return

        self.dlTable.setUpdatesEnabled(False)
        try:
            self.dlTable.setRowCount(0)
            for r in rows:
                row_i = self.dlTable.rowCount()
                self.dlTable.insertRow(row_i)
                self.dlTable.setItem(row_i, 0, _table_item(r.start_time))
                self.dlTable.setItem(row_i, 1, _table_item(r.filename))
                size_item = _table_item(
                    _fmt_bytes(r.total_bytes),
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                )
                size_item.setData(
                    Qt.ItemDataRole.UserRole, r.total_bytes
                )  # for numeric sort
                self.dlTable.setItem(row_i, 2, size_item)
                self.dlTable.setItem(
                    row_i,
                    3,
                    _table_item(tr(_DL_STATE_KEY.get(r.state, "dl_in_progress"))),
                )
                self.dlTable.setItem(row_i, 4, _table_item(r.referrer_domain))
                self.dlTable.setItem(row_i, 5, _table_item(r.url))
        finally:
            self.dlTable.setUpdatesEnabled(True)

        self.dlTable.resizeColumnToContents(0)
        self.dlTable.resizeColumnToContents(2)
        self._filter_table(self.dlTable, self.dlFilterInput.text())
        self.status.showMessage(f"Downloads: {len(rows)}")

    # ── Activity heatmap ──────────────────────────────────────────────────────

    def on_load_heatmap(self):
        history_db = self._require_history_db()
        if history_db is None:
            return

        try:
            data = query_visit_heatmap(history_db, days=self.hmDays.value())
        except Exception as e:
            QMessageBox.critical(self, tr("query_failed"), str(e))
            return

        self._build_heatmap_cells(data)

    def _build_heatmap_cells(self, data: dict[str, int]) -> None:
        from datetime import date as _date

        today = _date.today()
        days = self.hmDays.value()
        start_d = today - timedelta(days=days - 1)

        # Snap to Monday of start week
        first_monday = start_d - timedelta(days=start_d.weekday())  # weekday(): Mon=0
        total_days = (today - first_monday).days + 1
        n_weeks = (total_days + 6) // 7

        max_count = max(data.values(), default=1)

        # Resize table
        self.hmTable.setColumnCount(n_weeks)

        # Column headers: show month name at first week of each month
        last_month = -1
        for col in range(n_weeks):
            week_start = first_monday + timedelta(weeks=col)
            if week_start.month != last_month:
                last_month = week_start.month
                self.hmTable.setHorizontalHeaderItem(
                    col, QTableWidgetItem(week_start.strftime("%b"))
                )
            else:
                self.hmTable.setHorizontalHeaderItem(col, QTableWidgetItem(""))

        # Fill cells: row = weekday (Mon=0), col = week index
        for day_idx in range(n_weeks * 7):
            d = first_monday + timedelta(days=day_idx)
            col = day_idx // 7
            row = day_idx % 7  # Mon=0 … Sun=6

            item = QTableWidgetItem()
            item.setFlags(Qt.ItemFlag.ItemIsEnabled)

            if d < start_d or d > today:
                item.setBackground(QBrush(QColor(245, 245, 245)))
                item.setFlags(Qt.ItemFlag.NoItemFlags)
            else:
                date_str = d.isoformat()
                count = data.get(date_str, 0)
                item.setBackground(QBrush(_heatmap_color(count, max_count)))
                item.setToolTip(f"{date_str}\n{tr('hm_visits', n=count)}")
                item.setData(Qt.ItemDataRole.UserRole, date_str)

            self.hmTable.setItem(row, col, item)

        self.status.showMessage(
            f"Activity loaded — {sum(data.values())} total visits over {days} days"
        )

    def _on_heatmap_click(self, row: int, col: int):
        """Load the clicked day's history into the History tab."""
        item = self.hmTable.item(row, col)
        if item is None:
            return
        date_str = item.data(Qt.ItemDataRole.UserRole)
        if not date_str:
            return
        try:
            d = date.fromisoformat(date_str)
        except ValueError:
            return
        qt_d = QDate(d.year, d.month, d.day)
        self.dateStart.setDate(qt_d)
        self.dateEnd.setDate(qt_d)
        self.timeStart.setTime(QTime(0, 0))
        self.timeEnd.setTime(QTime(23, 59))
        self.tabs.setCurrentIndex(_TAB_HISTORY)
        self.on_search()

    # ── Domain stats ──────────────────────────────────────────────────────────

    def on_load_stats(self):
        history_db = self._require_history_db()
        if history_db is None:
            return

        start_dt = datetime.combine(
            self.stDateStart.date().toPython(), datetime.min.time()
        )
        end_dt = datetime.combine(self.stDateEnd.date().toPython(), datetime.max.time())
        if end_dt < start_dt:
            QMessageBox.warning(self, tr("invalid_range"), tr("invalid_range_msg"))
            return

        try:
            stats = query_domain_stats(history_db, start_dt, end_dt)
        except Exception as e:
            QMessageBox.critical(self, tr("query_failed"), str(e))
            return

        sorting_enabled = self.stTable.isSortingEnabled()
        self.stTable.setSortingEnabled(False)
        self.stTable.setUpdatesEnabled(False)
        try:
            self.stTable.setRowCount(0)
            for rank, s in enumerate(stats, 1):
                row_i = self.stTable.rowCount()
                self.stTable.insertRow(row_i)

                def _num_item(n: int) -> QTableWidgetItem:
                    it = QTableWidgetItem()
                    it.setData(Qt.ItemDataRole.DisplayRole, n)
                    it.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                    it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    return it

                self.stTable.setItem(row_i, 0, _num_item(rank))
                self.stTable.setItem(row_i, 1, _table_item(s.domain))
                self.stTable.setItem(row_i, 2, _num_item(s.visits))
                self.stTable.setItem(row_i, 3, _num_item(s.typed))
                self.stTable.setItem(row_i, 4, _table_item(s.last_visit))
        finally:
            self.stTable.setUpdatesEnabled(True)
            self.stTable.setSortingEnabled(sorting_enabled)

        self.status.showMessage(f"Stats: {len(stats)} domains")

    # ── Privacy audit ─────────────────────────────────────────────────────────

    def on_scan_privacy(self):
        prof_dir = self._profile_dir()
        if prof_dir is None:
            QMessageBox.warning(self, tr("edge_not_found"), tr("edge_not_found_msg"))
            return

        prefs_path = prof_dir / "Preferences"
        if not prefs_path.exists():
            QMessageBox.information(self, tr("tab_privacy"), tr("pv_prefs_not_found"))
            return

        settings = read_privacy_settings(prefs_path)

        _WARN_BG = QColor(255, 243, 224)  # light orange
        _SAFE_BG = QColor(232, 245, 233)  # light green

        self.pvTable.setUpdatesEnabled(False)
        try:
            self.pvTable.setRowCount(0)
            for s in settings:
                row_i = self.pvTable.rowCount()
                self.pvTable.insertRow(row_i)

                # Determine status
                if s.value is None:
                    status_text = tr("pv_unknown")
                    bg = None
                elif s.safe_when_false is None:
                    status_text = tr("pv_neutral")
                    bg = None
                else:
                    is_on = bool(s.value)
                    if s.safe_when_false:
                        if is_on:
                            status_text = tr("pv_warn")
                            bg = _WARN_BG
                        else:
                            status_text = tr("pv_safe")
                            bg = _SAFE_BG
                    else:
                        status_text = tr("pv_neutral")
                        bg = None

                val_text = "" if s.value is None else str(s.value)

                for col, text in enumerate(
                    [s.label, status_text, val_text, s.description]
                ):
                    item = _table_item(text)
                    if bg:
                        item.setBackground(QBrush(bg))
                    self.pvTable.setItem(row_i, col, item)
        finally:
            self.pvTable.setUpdatesEnabled(True)

        self.pvTable.resizeRowsToContents()
        self.status.showMessage(
            f"Privacy scan complete — {len(settings)} settings checked"
        )

    # ── Bookmarks audit ───────────────────────────────────────────────────────

    def on_scan_bookmarks(self):
        prof_dir = self._profile_dir()
        if prof_dir is None:
            QMessageBox.warning(self, tr("edge_not_found"), tr("edge_not_found_msg"))
            return

        bm_path = prof_dir / "Bookmarks"
        if not bm_path.exists():
            QMessageBox.information(self, tr("tab_bookmarks"), tr("bm_not_found"))
            return

        bookmarks = read_bookmarks(bm_path)

        # Find duplicates
        url_counter = Counter(b.url for b in bookmarks if b.url)
        dup_urls = {url: count for url, count in url_counter.items() if count > 1}

        # Summary
        self.bmSummaryLabel.setText(
            tr("bm_summary", total=len(bookmarks), dups=len(dup_urls))
        )

        _DUP_BG = QColor(255, 243, 224)

        # Duplicates table
        if isinstance(self.bmDupBoxLabel, QGroupBox):
            self.bmDupBoxLabel.setTitle(tr("bm_dup_section", n=len(dup_urls)))

        self.bmDupTable.setUpdatesEnabled(False)
        try:
            self.bmDupTable.setRowCount(0)
            if not dup_urls:
                self.bmDupTable.insertRow(0)
                self.bmDupTable.setItem(0, 0, _table_item(tr("bm_no_dups")))
            else:
                # Collect folder paths per URL
                url_folders: dict[str, list[str]] = {}
                url_titles: dict[str, str] = {}
                for b in bookmarks:
                    if b.url in dup_urls:
                        url_folders.setdefault(b.url, []).append(b.folder or "—")
                        url_titles.setdefault(b.url, b.title)

                for url, count in sorted(dup_urls.items(), key=lambda x: -x[1]):
                    row_i = self.bmDupTable.rowCount()
                    self.bmDupTable.insertRow(row_i)
                    folders_str = " | ".join(url_folders.get(url, []))
                    for col, text in enumerate([url, str(count), folders_str]):
                        item = _table_item(text)
                        item.setBackground(QBrush(_DUP_BG))
                        self.bmDupTable.setItem(row_i, col, item)
        finally:
            self.bmDupTable.setUpdatesEnabled(True)

        # All bookmarks table
        if isinstance(self.bmAllBoxLabel, QGroupBox):
            self.bmAllBoxLabel.setTitle(tr("bm_all_section", n=len(bookmarks)))

        self.bmAllTable.setUpdatesEnabled(False)
        try:
            self.bmAllTable.setRowCount(0)
            for b in bookmarks:
                row_i = self.bmAllTable.rowCount()
                self.bmAllTable.insertRow(row_i)
                is_dup = b.url in dup_urls
                for col, text in enumerate([b.title, b.url, b.folder, b.added]):
                    item = _table_item(text)
                    if is_dup:
                        item.setBackground(QBrush(_DUP_BG))
                    self.bmAllTable.setItem(row_i, col, item)
        finally:
            self.bmAllTable.setUpdatesEnabled(True)

        self._filter_table(self.bmAllTable, self.bmFilterInput.text())
        self.status.showMessage(
            f"Bookmarks: {len(bookmarks)} total, {len(dup_urls)} duplicate URLs"
        )


# ---------------------------------------------------------------------------
# About dialog
# ---------------------------------------------------------------------------


def _show_about_dialog(parent, qsettings: QSettings) -> None:
    dlg = QDialog(parent)
    dlg.setWindowTitle(tr("title"))
    dlg.setModal(True)
    lay = QVBoxLayout(dlg)

    title_lbl = QLabel(tr("title"))
    title_lbl.setStyleSheet("font-size: 18px; font-weight: 700;")
    lay.addWidget(title_lbl)

    try:
        _version = pkg_version("edge-history-finder")
    except Exception:
        _version = "dev"
    version_lbl = QLabel(f"Version {_version}")
    version_lbl.setStyleSheet("color: #666; font-size: 11px;")
    lay.addWidget(version_lbl)

    lay.addWidget(
        QLabel(
            "System design and intent by Thomas Radman · "
            "Code generated by OpenClaw & opencode using OpenAI GPT 5.2 Codex & Anthropic Sonnet 4.5"
        )
    )
    lay.addSpacing(10)

    features_title = QLabel("Features:")
    features_title.setStyleSheet("font-weight: bold;")
    lay.addWidget(features_title)

    for text in [
        "• <b>History Search:</b> Find lost URLs by time window, exclude common sites,\n"
        "  filter by weekday, and search only typed URLs.",
        "• <b>Closed Tabs Finder:</b> Recover groups of tabs closed together.\n"
        "  Detects tab groups by clustering URLs visited within seconds.",
        "• <b>Downloads:</b> Search your full download history by date range.",
        "• <b>Activity:</b> GitHub-style heatmap of daily browsing activity.\n"
        "  Click any cell to jump to that day's history.",
        "• <b>Stats:</b> Top domains by visit count for any date range.",
        "• <b>Privacy Audit:</b> Check which Edge data-collection settings are active.",
        "• <b>Bookmarks:</b> Find duplicate bookmarks across your profile.",
    ]:
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #333;")
        lay.addWidget(lbl)

    lay.addSpacing(10)
    tip = QLabel(
        "Tip: Right-click results to copy / exclude domains.\n"
        "Privacy: runs locally, reads Edge data via temp copy — never writes or sends anything."
    )
    tip.setStyleSheet("color: #555;")
    lay.addWidget(tip)

    gh = QLabel(
        '<a href="https://github.com/tradmangh/edge-history-finder/issues/new/choose">'
        "Report bugs or request features on GitHub</a>"
    )
    gh.setOpenExternalLinks(True)
    gh.setStyleSheet("color: #0066cc;")
    lay.addWidget(gh)

    cb = QCheckBox(tr("dont_show_again"))
    cb.setChecked(not bool(qsettings.value("showSplash", True)))
    lay.addWidget(cb)

    bb = QDialogButtonBox(QDialogButtonBox.Ok)

    def _accept():
        qsettings.setValue("showSplash", not cb.isChecked())
        dlg.accept()

    bb.accepted.connect(_accept)
    lay.addWidget(bb)
    dlg.exec()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> int:
    app = QApplication(sys.argv)

    qs = QSettings("tradm", "EdgeHistoryFinder")
    show = qs.value("showSplash", True)
    if isinstance(show, str):
        show = show.lower() in ("1", "true", "yes")

    w = MainWindow()
    if bool(show):
        _show_about_dialog(w, qs)
    w.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
