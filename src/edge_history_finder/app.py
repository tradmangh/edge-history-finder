from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime, time
from pathlib import Path
from typing import List
from urllib.parse import urlparse

from PySide6.QtCore import Qt, QLocale, QSettings, QTimer
from PySide6.QtGui import QGuiApplication, QAction, QColor, QFont, QPainter, QPixmap
from PySide6.QtWidgets import QSplashScreen
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QStatusBar,
    QDateEdit,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from .history import query_history, windows_edge_user_data_dir, list_profiles


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
    },
    "de": {
        "title": "Edge History Finder",
        "edge_user_data": "Edge User Data",
        "profile": "Profil",
        "date": "Datum",
        "time": "Uhrzeit",
        "from": "Von",
        "to": "Bis",
        "limit": "Limit",
        "negative_filters": "Negativfilter",
        "exclude_placeholder": "Exclude contains… (z.B. google.com)",
        "add": "Add",
        "weekdays": "Wochentage",
        "mode": "Mode",
        "typed_only": "Typed only",
        "search": "Search",
        "search_tip": "Optional: manuelles Refresh (Auto-Refresh ist aktiv)",
        "copy_urls": "Copy selected URL(s)",
        "exclude_domains": "Exclude {n} domains",
        "exclude_domain": "Exclude domain",
        "exclude_prefixes": "Exclude {n} URL prefixes",
        "exclude_prefix": "Exclude this URL prefix",
        "copy_url": "Copy URL",
        "remove_selected": "Remove selected",
        "clear_all": "Clear all",
        "ready": "Bereit",
        "edge_not_found": "Edge nicht gefunden",
        "edge_not_found_msg": "Edge User Data wurde über LOCALAPPDATA nicht gefunden.",
        "history_not_found": "History nicht gefunden",
        "invalid_range": "Ungültiger Zeitraum",
        "invalid_range_msg": "Ende liegt vor Start.",
        "query_failed": "Query fehlgeschlagen",
        "col_time": "Zeit",
        "col_domain": "Domain",
        "col_gq": "Google Query",
        "col_title": "Titel",
        "col_url": "URL",
    },
}


def tr(key: str, **fmt) -> str:
    s = _T.get(_LANG, _T["en"]).get(key, _T["en"].get(key, key))
    try:
        return s.format(**fmt)
    except Exception:
        return s


@dataclass
class Settings:
    excludes: List[str]


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
        wd = s.value("weekdays", [0,1,2,3,4,5,6], list)
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
        st = s.value("timeStart", "12:00")
        en = s.value("timeEnd", "19:00")
        try:
            hh, mm = [int(x) for x in str(st).split(":", 1)]
            self.timeStart.setTime(time(hh, mm))
        except Exception:
            pass
        try:
            hh, mm = [int(x) for x in str(en).split(":", 1)]
            self.timeEnd.setTime(time(hh, mm))
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
        # weekdays mapping 0..6
        wds: List[int] = []
        if self.wd_sun.isChecked(): wds.append(0)
        if self.wd_mon.isChecked(): wds.append(1)
        if self.wd_tue.isChecked(): wds.append(2)
        if self.wd_wed.isChecked(): wds.append(3)
        if self.wd_thu.isChecked(): wds.append(4)
        if self.wd_fri.isChecked(): wds.append(5)
        if self.wd_sat.isChecked(): wds.append(6)
        s.setValue("weekdays", wds)

    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr("title"))
        self.resize(1050, 700)

        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)

        # --- Controls
        controls = QWidget()
        form = QFormLayout(controls)
        layout.addWidget(controls)

        self.profile = QComboBox()
        self.profilePath = QLineEdit()
        self.profilePath.setReadOnly(True)

        user_data = windows_edge_user_data_dir()
        if user_data is None:
            self.profilePath.setPlaceholderText("Windows Edge User Data not found. Set path manually later.")
        else:
            self.profilePath.setText(str(user_data))
            for p in list_profiles(user_data):
                self.profile.addItem(p)
        self.profile.currentIndexChanged.connect(lambda _i: (self._update_status(), self._save_settings(), self._schedule_refresh()))

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

        # auto-refresh triggers
        self.dateStart.dateChanged.connect(lambda _d: self._schedule_refresh())
        self.dateEnd.dateChanged.connect(lambda _d: self._schedule_refresh())
        self.timeStart.timeChanged.connect(lambda _t: self._schedule_refresh())
        self.timeEnd.timeChanged.connect(lambda _t: self._schedule_refresh())
        self.limit.valueChanged.connect(lambda _v: self._schedule_refresh())

        form.addRow(tr("edge_user_data"), self.profilePath)
        form.addRow(tr("profile"), self.profile)

        row_dt = QWidget(); row_dt_l = QHBoxLayout(row_dt); row_dt_l.setContentsMargins(0,0,0,0)
        row_dt_l.addWidget(QLabel(tr("from"))); row_dt_l.addWidget(self.dateStart)
        row_dt_l.addWidget(QLabel(tr("to"))); row_dt_l.addWidget(self.dateEnd)
        row_dt_l.addStretch(1)
        form.addRow(tr("date"), row_dt)

        row_t = QWidget(); row_t_l = QHBoxLayout(row_t); row_t_l.setContentsMargins(0,0,0,0)
        row_t_l.addWidget(QLabel(tr("from"))); row_t_l.addWidget(self.timeStart)
        row_t_l.addWidget(QLabel(tr("to"))); row_t_l.addWidget(self.timeEnd)
        row_t_l.addStretch(1)
        form.addRow(tr("time"), row_t)

        form.addRow(tr("limit"), self.limit)

        self.typedOnly = QCheckBox(tr("typed_only"))
        self.typedOnly.setChecked(True)
        self.typedOnly.stateChanged.connect(lambda _s: (self._update_status(), self._save_settings(), self._schedule_refresh()))
        form.addRow(tr("mode"), self.typedOnly)

        # Weekday filter (SQLite %w: 0=Sun..6=Sat)
        wd_row = QWidget(); wd_l = QHBoxLayout(wd_row); wd_l.setContentsMargins(0,0,0,0)
        self.wd_mon = QCheckBox("Mo")
        self.wd_tue = QCheckBox("Di")
        self.wd_wed = QCheckBox("Mi")
        self.wd_thu = QCheckBox("Do")
        self.wd_fri = QCheckBox("Fr")
        self.wd_sat = QCheckBox("Sa")
        self.wd_sun = QCheckBox("So")
        for cb in [self.wd_mon,self.wd_tue,self.wd_wed,self.wd_thu,self.wd_fri,self.wd_sat,self.wd_sun]:
            cb.setChecked(True)
            cb.stateChanged.connect(lambda _s: (self._save_settings(), self._schedule_refresh()))
            wd_l.addWidget(cb)
        wd_l.addStretch(1)
        form.addRow(tr("weekdays"), wd_row)

        # --- Excludes
        ex_wrap = QWidget()
        ex_l = QHBoxLayout(ex_wrap)
        ex_l.setContentsMargins(0,0,0,0)
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
        layout.addWidget(self.excludeList)

        # --- Action buttons
        btns = QWidget(); btns_l = QHBoxLayout(btns); btns_l.setContentsMargins(0,0,0,0)
        self.searchBtn = QPushButton(tr("search"))
        self.searchBtn.setToolTip(tr("search_tip"))
        btns_l.addWidget(self.searchBtn)
        btns_l.addStretch(1)
        layout.addWidget(btns)

        # --- Results
        # Columns: time, domain, google query (if any), title, url
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([tr("col_time"), tr("col_domain"), tr("col_gq"), tr("col_title"), tr("col_url")])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.table.setWordWrap(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        layout.addWidget(self.table, 1)

        # wire
        # debounce auto-refresh
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.timeout.connect(self.on_search)

        self.excludeAdd.clicked.connect(self.on_add_exclude)
        self.excludeInput.returnPressed.connect(self.on_add_exclude)
        self.excludeRemove.clicked.connect(self.on_remove_exclude)
        self.excludeList.customContextMenuRequested.connect(self.on_exclude_context_menu)
        self.searchBtn.clicked.connect(self.on_search)

        # status bar (must exist before _update_status)
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage(tr("ready"))

        # persistent settings
        self._qsettings = QSettings("tradm", "EdgeHistoryFinder")
        self._load_settings()
        self._update_status()
        self.table.itemDoubleClicked.connect(self.on_double_click)
        self.table.customContextMenuRequested.connect(self.on_table_context_menu)

        # status bar (initialized earlier)

    def excludes(self) -> List[str]:
        return [self.excludeList.item(i).text().strip() for i in range(self.excludeList.count()) if self.excludeList.item(i).text().strip()]

    def _schedule_refresh(self):
        # Debounced auto-refresh to avoid hammering SQLite while typing/clicking.
        self._refresh_timer.start(250)

    def on_add_exclude(self):
        t = self.excludeInput.text().strip()
        if not t:
            return
        # avoid dups
        existing = set(self.excludes())
        if t not in existing:
            self.excludeList.addItem(t)
        self.excludeInput.clear()
        self._update_status()
        self._save_settings()
        self._schedule_refresh()

    def on_remove_exclude(self):
        for it in self.excludeList.selectedItems():
            row = self.excludeList.row(it)
            self.excludeList.takeItem(row)
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

    # selection changed: nothing to do (copy happens via context menu / double-click)
    def on_sel_changed(self):
        return

    def _selected_urls(self) -> List[str]:
        rows = sorted({it.row() for it in self.table.selectedItems()})
        out: List[str] = []
        for r in rows:
            it = self.table.item(r, 4)
            if not it:
                continue
            u = it.text().strip()
            if u:
                out.append(u)
        return out

    def _current_url(self) -> str | None:
        urls = self._selected_urls()
        return urls[0] if urls else None

    def on_copy(self):
        urls = self._selected_urls()
        if not urls:
            return
        # If multiple rows selected, copy as newline-separated list.
        QGuiApplication.clipboard().setText("\n".join(urls))

    def on_double_click(self, _item):
        # Doppelklick = URL kopieren
        self.on_copy()

    def _add_exclude_value(self, value: str):
        value = value.strip()
        if not value:
            return
        existing = set(self.excludes())
        if value not in existing:
            self.excludeList.addItem(value)

    def _add_exclude_values(self, values: List[str]):
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

        # Exclude domains of selected
        hosts: List[str] = []
        for u in urls:
            try:
                host = urlparse(u).netloc
            except Exception:
                host = ""
            if host:
                hosts.append(host)
        hosts = sorted(set(hosts))
        if hosts:
            label = tr("exclude_domain") if len(hosts) == 1 else tr("exclude_domains", n=len(hosts))
            act_ex_domains = QAction(label, self)
            act_ex_domains.triggered.connect(lambda: self._add_exclude_values(hosts))
            menu.addAction(act_ex_domains)

        # Exclude URL prefixes of selected
        prefixes: List[str] = []
        for u in urls:
            try:
                p = urlparse(u)
                prefix = f"{p.scheme}://{p.netloc}{p.path}"
            except Exception:
                prefix = ""
            if prefix:
                prefixes.append(prefix)
        prefixes = sorted(set(prefixes))
        if prefixes:
            label = tr("exclude_prefix") if len(prefixes) == 1 else tr("exclude_prefixes", n=len(prefixes))
            act_ex_prefixes = QAction(label, self)
            act_ex_prefixes.triggered.connect(lambda: self._add_exclude_values(prefixes))
            menu.addAction(act_ex_prefixes)

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _update_status(self, result_count: int | None = None):
        typed = "typed-only" if self.typedOnly.isChecked() else "all-visits"
        ex_n = self.excludeList.count()
        prof = self.profile.currentText() or "Default"
        # if result_count is None, keep last known
        if result_count is not None:
            self._last_result_count = result_count
        rc = getattr(self, "_last_result_count", 0)
        self.status.showMessage(f"Profile: {prof} | Mode: {typed} | Excludes: {ex_n} | Results: {rc}")

    def on_search(self):
        user_data = windows_edge_user_data_dir()
        if user_data is None:
            QMessageBox.warning(self, tr("edge_not_found"), tr("edge_not_found_msg"))
            return
        profile = self.profile.currentText() or "Default"
        history_db = Path(user_data) / profile / "History"
        if not history_db.exists():
            QMessageBox.warning(self, tr("history_not_found"), f"History DB not found: {history_db}")
            return

        ds = self.dateStart.date().toPython()
        de = self.dateEnd.date().toPython()
        ts = self.timeStart.time().toPython()
        te = self.timeEnd.time().toPython()

        start_dt = datetime.combine(ds, ts)
        end_dt = datetime.combine(de, te)
        if end_dt < start_dt:
            QMessageBox.warning(self, tr("invalid_range"), tr("invalid_range_msg"))
            return

        # SQLite weekday mapping: 0=Sun..6=Sat
        weekdays: List[int] = []
        if self.wd_sun.isChecked(): weekdays.append(0)
        if self.wd_mon.isChecked(): weekdays.append(1)
        if self.wd_tue.isChecked(): weekdays.append(2)
        if self.wd_wed.isChecked(): weekdays.append(3)
        if self.wd_thu.isChecked(): weekdays.append(4)
        if self.wd_fri.isChecked(): weekdays.append(5)
        if self.wd_sat.isChecked(): weekdays.append(6)

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
                if u.netloc.endswith("google.com") or u.netloc.endswith("google.at"):
                    if u.path.startswith("/search"):
                        from urllib.parse import parse_qs

                        qs = parse_qs(u.query)
                        qv = qs.get("q")
                        if qv:
                            gq = qv[0]
            except Exception:
                pass

            self.table.setItem(row_i, 1, QTableWidgetItem(domain))
            self.table.setItem(row_i, 2, QTableWidgetItem(gq))
            self.table.setItem(row_i, 3, QTableWidgetItem(r.title))
            self.table.setItem(row_i, 4, QTableWidgetItem(r.url))

        if rows:
            self.table.selectRow(0)

        self._update_status(result_count=len(rows))


def _make_splash() -> QSplashScreen:
    w, h = 700, 220
    pm = QPixmap(w, h)
    pm.fill(QColor("#111827"))

    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)

    p.setPen(QColor("#E5E7EB"))
    p.setFont(QFont("Segoe UI", 18, QFont.Bold))
    p.drawText(24, 55, tr("title"))

    p.setFont(QFont("Segoe UI", 10))
    p.setPen(QColor("#9CA3AF"))
    p.drawText(24, 90, "Written by Thomas Radman")
    p.drawText(24, 112, "Co-authored by OpenClaw / OpenAI Codex 5.2")

    p.setPen(QColor("#6B7280"))
    p.drawText(24, 155, "Tip: Right-click results to copy / exclude domains.")
    p.drawText(24, 175, "Privacy: runs locally, reads Edge History SQLite via temp copy.")

    p.end()

    splash = QSplashScreen(pm)
    splash.setWindowFlag(Qt.WindowStaysOnTopHint, True)
    return splash


def main() -> int:
    app = QApplication(sys.argv)

    splash = _make_splash()
    splash.show()
    app.processEvents()

    w = MainWindow()
    w.show()
    splash.finish(w)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
