from __future__ import annotations

import sys
from datetime import datetime, time, timedelta
from importlib.metadata import version as pkg_version
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from PySide6.QtCore import Qt, QLocale, QSettings, QTimer
from PySide6.QtGui import (
    QAction,
    QColor,
    QFont,
    QGuiApplication,
    QKeySequence,
    QShortcut,
)
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDateEdit,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSpinBox,
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
    query_history,
    windows_edge_user_data_dir,
)

# tgSortBy combo indices — using constants avoids fragile currentIndex() == 1 checks
_SORT_DATETIME = 0
_SORT_ALPHA = 1


def _lang() -> str:
    # OS language → 'de' or 'en'
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
        "title": "Edge History Finder",
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
        "ready": "Ready",
        "dont_show_again": "Don't show again",
        "edge_not_found": "Edge not found",
        "edge_not_found_msg": "Could not find Edge user data directory via LOCALAPPDATA.",
        "history_not_found": "History not found",
        "invalid_range": "Invalid range",
        "invalid_range_msg": "End datetime is before start datetime.",
        "query_failed": "Query failed",
        "col_time": "Time",
        "col_domain": "Domain",
        "col_gq": "Google Query",
        "col_title": "Title",
        "col_url": "URL",
        "tab_groups": "Tab Groups",
        "tab_groups_btn": "Find Tab Groups",
        "tab_groups_urls": "{n} URLs",
        "history": "History",
        "ClosedTabsFinder": "Closed Tabs Finder",
        "min_urls_label": "Min URLs:",
        "window_sec_label": "Window (sec):",
        "deduplicate": "Deduplicate URLs",
        "sort_by": "Sort by:",
        "sort_datetime": "Date/Time (default)",
        "sort_alpha": "Alphabetical",
        "no_tab_groups": "No tab groups found",
        "tab_groups_header": "Tab Groups (click to expand)",
        "help_menu": "Help",
        "about_action": "About",
    },
    "de": {
        "title": "Edge History Finder",
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
        "ready": "Bereit",
        "dont_show_again": "Nicht mehr anzeigen",
        "edge_not_found": "Edge nicht gefunden",
        "edge_not_found_msg": "Edge User Data wurde über LOCALAPPDATA nicht gefunden.",
        "history_not_found": "History nicht gefunden",
        "invalid_range": "Ungültiger Zeitraum",
        "invalid_range_msg": "Ende liegt vor Start.",
        "query_failed": "Abfrage fehlgeschlagen",
        "col_time": "Zeit",
        "col_domain": "Domain",
        "col_gq": "Google-Suchbegriff",
        "col_title": "Titel",
        "col_url": "URL",
        "tab_groups": "Tab-Gruppen",
        "tab_groups_btn": "Tab-Gruppen finden",
        "tab_groups_urls": "{n} URLs",
        "history": "Chronik",
        "ClosedTabsFinder": "Geschlossene Tabs Finder",
        "min_urls_label": "Min. URLs:",
        "window_sec_label": "Fenster (Sek.):",
        "deduplicate": "URLs deduplizieren",
        "sort_by": "Sortieren nach:",
        "sort_datetime": "Datum/Uhrzeit (Standard)",
        "sort_alpha": "Alphabetisch",
        "no_tab_groups": "Keine Tab-Gruppen gefunden",
        "tab_groups_header": "Tab-Gruppen (klicken zum Aufklappen)",
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


class MainWindow(QMainWindow):
    def _load_settings(self):
        s = self._qsettings

        # excludes
        ex = s.value("excludes", [], list)
        if isinstance(ex, str):
            ex = [ex]
        if ex:
            self.excludeList.clear()
            for v in ex:
                if v and str(v).strip():
                    self.excludeList.addItem(str(v).strip())

        # typedOnly
        to = s.value("typedOnly", True)
        if isinstance(to, str):
            to = to.lower() in ("1", "true", "yes")
        self.typedOnly.setChecked(bool(to))

        # weekdays
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

        # profile index
        pi = s.value("profileIndex", 0)
        try:
            pi = int(pi)
        except Exception:
            pi = 0
        if 0 <= pi < self.profile.count():
            self.profile.setCurrentIndex(pi)

        # time window
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

        # limit
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

    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr("title"))
        self.resize(1050, 700)

        # Cached once at startup — avoids repeated filesystem hits on every query.
        # Restart the app if Edge is installed/moved while it is running.
        self._user_data_dir: Path | None = windows_edge_user_data_dir()
        self._last_result_count: int = 0

        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)

        # ── Tab widget ──────────────────────────────────────────────────────────
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)

        # ── Tab 1: History ──────────────────────────────────────────────────────
        tab_history = QWidget()
        tab_history_layout = QVBoxLayout(tab_history)

        controls = QWidget()
        form = QFormLayout(controls)
        tab_history_layout.addWidget(controls)

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
        tab_history_layout.addWidget(self.excludeList)

        btns = QWidget()
        btns_l = QHBoxLayout(btns)
        btns_l.setContentsMargins(0, 0, 0, 0)
        self.searchBtn = QPushButton(tr("search"))
        self.searchBtn.setToolTip(tr("search_tip"))
        btns_l.addWidget(self.searchBtn)
        btns_l.addStretch(1)
        tab_history_layout.addWidget(btns)

        # Results table: Time | Domain | Google Query | Title | URL
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            [
                tr("col_time"),
                tr("col_domain"),
                tr("col_gq"),
                tr("col_title"),
                tr("col_url"),
            ]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.table.setWordWrap(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        tab_history_layout.addWidget(self.table, 1)

        # Ctrl+C copies selected URL(s) from the results table
        QShortcut(QKeySequence.StandardKey.Copy, self.table).activated.connect(
            self.on_copy
        )

        self.tabs.addTab(tab_history, tr("history"))

        # ── Tab 2: Closed Tabs Finder ───────────────────────────────────────────
        tab_closed = QWidget()
        tab_closed_layout = QVBoxLayout(tab_closed)

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
        self.tgMinUrls.setToolTip(tr("min_urls_label"))
        tg_row_l.addWidget(self.tgMinUrls)

        tg_row_l.addWidget(QLabel("  " + tr("window_sec_label")))
        self.tgWindowSeconds = QSpinBox()
        self.tgWindowSeconds.setRange(1, 600)
        self.tgWindowSeconds.setValue(60)
        self.tgWindowSeconds.setToolTip(tr("window_sec_label"))
        tg_row_l.addWidget(self.tgWindowSeconds)
        tg_row_l.addStretch(1)

        tg_form.addRow(tr("tab_groups"), tg_row)

        tg_options_row = QWidget()
        tg_options_l = QHBoxLayout(tg_options_row)
        tg_options_l.setContentsMargins(0, 0, 0, 0)

        self.tgDeduplicate = QCheckBox(tr("deduplicate"))
        self.tgDeduplicate.setChecked(True)
        tg_options_l.addWidget(self.tgDeduplicate)

        tg_options_l.addWidget(QLabel("  " + tr("sort_by")))
        self.tgSortBy = QComboBox()
        self.tgSortBy.addItem(tr("sort_datetime"))  # index _SORT_DATETIME = 0
        self.tgSortBy.addItem(tr("sort_alpha"))  # index _SORT_ALPHA    = 1
        tg_options_l.addWidget(self.tgSortBy)
        tg_options_l.addStretch(1)

        tg_form.addRow("", tg_options_row)
        tab_closed_layout.addWidget(tg_section)

        self.tgResults = QTreeWidget()
        self.tgResults.setHeaderLabels([tr("tab_groups_header")])
        self.tgResults.setAlternatingRowColors(True)
        self.tgResults.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tgResults.customContextMenuRequested.connect(self.on_tg_context_menu)
        tab_closed_layout.addWidget(self.tgResults, 1)

        self.tabs.addTab(tab_closed, tr("ClosedTabsFinder"))
        self.tabs.currentChanged.connect(self._on_tab_changed)

        # ── Timers ──────────────────────────────────────────────────────────────
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.timeout.connect(self.on_search)

        self._tg_refresh_timer = QTimer(self)
        self._tg_refresh_timer.setSingleShot(True)
        self._tg_refresh_timer.timeout.connect(self.on_find_tab_groups)

        # ── Wiring ──────────────────────────────────────────────────────────────
        self.excludeAdd.clicked.connect(self.on_add_exclude)
        self.excludeInput.returnPressed.connect(self.on_add_exclude)
        self.excludeRemove.clicked.connect(self.on_remove_exclude)
        self.excludeList.customContextMenuRequested.connect(
            self.on_exclude_context_menu
        )
        self.searchBtn.clicked.connect(self.on_search)

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

        self.table.itemDoubleClicked.connect(self.on_double_click)
        self.table.customContextMenuRequested.connect(self.on_table_context_menu)

        # ── Status bar ──────────────────────────────────────────────────────────
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage(tr("ready"))

        # ── Persistent settings ─────────────────────────────────────────────────
        self._qsettings = QSettings("tradm", "EdgeHistoryFinder")

        # ── Menu ────────────────────────────────────────────────────────────────
        help_menu = self.menuBar().addMenu(tr("help_menu"))
        act_about = QAction(tr("about_action"), self)
        act_about.triggered.connect(lambda: _show_about_dialog(self, self._qsettings))
        help_menu.addAction(act_about)

        self._load_settings()
        self._update_status()

    # ── Helpers ─────────────────────────────────────────────────────────────────

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
        if index == 1:
            self.on_find_tab_groups()

    # ── Exclude list ─────────────────────────────────────────────────────────────

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

    # ── Table helpers ────────────────────────────────────────────────────────────

    def _selected_urls(self) -> list[str]:
        rows = sorted({it.row() for it in self.table.selectedItems()})
        out: list[str] = []
        for r in rows:
            it = self.table.item(r, 4)
            if it:
                u = it.text().strip()
                if u:
                    out.append(u)
        return out

    def on_copy(self):
        urls = self._selected_urls()
        if urls:
            QGuiApplication.clipboard().setText("\n".join(urls))

    def on_double_click(self, _item):
        self.on_copy()

    def _add_exclude_value(self, value: str):
        value = value.strip()
        if value and value not in set(self.excludes()):
            self.excludeList.addItem(value)

    def _add_exclude_values(self, values: list[str]):
        for v in values:
            self._add_exclude_value(v)

    def on_table_context_menu(self, pos):
        urls = self._selected_urls()
        if not urls:
            return

        menu = QMenu(self)

        act_copy = QAction(tr("copy_urls"), self)
        act_copy.triggered.connect(self.on_copy)
        menu.addAction(act_copy)

        hosts: list[str] = sorted(
            {urlparse(u).netloc for u in urls if urlparse(u).netloc}
        )
        if hosts:
            label = (
                tr("exclude_domain")
                if len(hosts) == 1
                else tr("exclude_domains", n=len(hosts))
            )
            act_ex = QAction(label, self)
            act_ex.triggered.connect(lambda: self._add_exclude_values(hosts))
            menu.addAction(act_ex)

        prefixes: list[str] = []
        for u in urls:
            try:
                p = urlparse(u)
                prefix = f"{p.scheme}://{p.netloc}{p.path}"
                if prefix:
                    prefixes.append(prefix)
            except Exception:
                pass
        prefixes = sorted(set(prefixes))
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

    # ── Status bar ───────────────────────────────────────────────────────────────

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

    # ── History search ───────────────────────────────────────────────────────────

    def on_search(self):
        user_data = self._user_data_dir
        if user_data is None:
            QMessageBox.warning(self, tr("edge_not_found"), tr("edge_not_found_msg"))
            return
        profile = self.profile.currentText() or "Default"
        history_db = Path(user_data) / profile / "History"
        if not history_db.exists():
            QMessageBox.warning(
                self, tr("history_not_found"), f"History DB not found: {history_db}"
            )
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

        # SQLite weekday mapping: 0=Sun..6=Sat
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

        # Batch all row inserts in one repaint cycle for performance
        self.table.setUpdatesEnabled(False)
        try:
            self.table.setRowCount(0)
            for r in rows:
                row_i = self.table.rowCount()
                self.table.insertRow(row_i)
                self.table.setItem(row_i, 0, QTableWidgetItem(r.local_time))

                domain = ""
                gq = ""
                try:
                    u = urlparse(r.url)
                    domain = u.netloc
                    # Match any Google TLD: google.com, google.de, google.co.uk, etc.
                    if u.path.startswith("/search") and (
                        ".google." in u.netloc or u.netloc.startswith("google.")
                    ):
                        qv = parse_qs(u.query).get("q")
                        if qv:
                            gq = qv[0]
                except Exception:
                    pass

                self.table.setItem(row_i, 1, QTableWidgetItem(domain))
                self.table.setItem(row_i, 2, QTableWidgetItem(gq))
                self.table.setItem(row_i, 3, QTableWidgetItem(r.title))
                self.table.setItem(row_i, 4, QTableWidgetItem(r.url))
        finally:
            self.table.setUpdatesEnabled(True)

        if rows:
            self.table.selectRow(0)
        self._update_status(result_count=len(rows))

    # ── Closed Tabs Finder ───────────────────────────────────────────────────────

    def on_find_tab_groups(self):
        user_data = self._user_data_dir
        if user_data is None:
            QMessageBox.warning(self, tr("edge_not_found"), tr("edge_not_found_msg"))
            return
        profile = self.profile.currentText() or "Default"
        history_db = Path(user_data) / profile / "History"
        if not history_db.exists():
            QMessageBox.warning(
                self, tr("history_not_found"), f"History DB not found: {history_db}"
            )
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
            deduped_count = len(urls)

            if sort_alphabetically:
                urls = sorted(urls)

            if deduplicate:
                header_text = f"{group.timestamp} — {deduped_count}/{total_count} URLs"
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
    ]:
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #333;")
        lay.addWidget(lbl)

    lay.addSpacing(10)

    tip = QLabel(
        "Tip: Right-click results to copy / exclude domains.\n"
        "Privacy: runs locally, reads Edge History SQLite via temp copy."
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
