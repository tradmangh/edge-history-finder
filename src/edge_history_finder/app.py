from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime, time
from pathlib import Path
from typing import List
from urllib.parse import urlparse

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QAction
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
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


@dataclass
class Settings:
    excludes: List[str]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Edge History Finder")
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

        form.addRow("Edge User Data", self.profilePath)
        form.addRow("Profil", self.profile)

        row_dt = QWidget(); row_dt_l = QHBoxLayout(row_dt); row_dt_l.setContentsMargins(0,0,0,0)
        row_dt_l.addWidget(QLabel("Von")); row_dt_l.addWidget(self.dateStart)
        row_dt_l.addWidget(QLabel("Bis")); row_dt_l.addWidget(self.dateEnd)
        row_dt_l.addStretch(1)
        form.addRow("Datum", row_dt)

        row_t = QWidget(); row_t_l = QHBoxLayout(row_t); row_t_l.setContentsMargins(0,0,0,0)
        row_t_l.addWidget(QLabel("Von")); row_t_l.addWidget(self.timeStart)
        row_t_l.addWidget(QLabel("Bis")); row_t_l.addWidget(self.timeEnd)
        row_t_l.addStretch(1)
        form.addRow("Uhrzeit", row_t)

        form.addRow("Limit", self.limit)

        self.typedOnly = QCheckBox("Typed only")
        self.typedOnly.setChecked(True)
        form.addRow("Mode", self.typedOnly)

        # --- Excludes
        ex_wrap = QWidget()
        ex_l = QHBoxLayout(ex_wrap)
        ex_l.setContentsMargins(0,0,0,0)
        self.excludeInput = QLineEdit()
        self.excludeInput.setPlaceholderText("Exclude contains… (e.g. google.com)")
        self.excludeAdd = QPushButton("Add")
        self.excludeRemove = QPushButton("Remove selected")
        ex_l.addWidget(self.excludeInput)
        ex_l.addWidget(self.excludeAdd)
        ex_l.addWidget(self.excludeRemove)
        form.addRow("Negativfilter", ex_wrap)

        self.excludeList = QListWidget()
        self.excludeList.addItem("google.com")
        self.excludeList.addItem("youtube.com")
        layout.addWidget(self.excludeList)

        # --- Action buttons
        btns = QWidget(); btns_l = QHBoxLayout(btns); btns_l.setContentsMargins(0,0,0,0)
        self.searchBtn = QPushButton("Search typed URLs")
        self.copyBtn = QPushButton("Copy selected URL")
        self.copyBtn.setEnabled(False)
        btns_l.addWidget(self.searchBtn)
        btns_l.addWidget(self.copyBtn)
        btns_l.addStretch(1)
        layout.addWidget(btns)

        # --- Results
        # Columns: time, domain, google query (if any), title, url
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Zeit", "Domain", "Google Query", "Titel", "URL"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.table.setWordWrap(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        layout.addWidget(self.table, 1)

        # wire
        self.excludeAdd.clicked.connect(self.on_add_exclude)
        self.excludeRemove.clicked.connect(self.on_remove_exclude)
        self.searchBtn.clicked.connect(self.on_search)
        self.copyBtn.clicked.connect(self.on_copy)
        self.table.itemSelectionChanged.connect(self.on_sel_changed)
        self.table.itemDoubleClicked.connect(self.on_double_click)
        self.table.customContextMenuRequested.connect(self.on_table_context_menu)

    def excludes(self) -> List[str]:
        return [self.excludeList.item(i).text().strip() for i in range(self.excludeList.count()) if self.excludeList.item(i).text().strip()]

    def on_add_exclude(self):
        t = self.excludeInput.text().strip()
        if not t:
            return
        # avoid dups
        existing = set(self.excludes())
        if t not in existing:
            self.excludeList.addItem(t)
        self.excludeInput.clear()

    def on_remove_exclude(self):
        for it in self.excludeList.selectedItems():
            row = self.excludeList.row(it)
            self.excludeList.takeItem(row)

    def on_sel_changed(self):
        self.copyBtn.setEnabled(len(self.table.selectedItems()) > 0)

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

        act_copy = QAction("Copy selected URL(s)", self)
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
            label = "Exclude domain" if len(hosts) == 1 else f"Exclude {len(hosts)} domains"
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
            label = "Exclude this URL prefix" if len(prefixes) == 1 else f"Exclude {len(prefixes)} URL prefixes"
            act_ex_prefixes = QAction(label, self)
            act_ex_prefixes.triggered.connect(lambda: self._add_exclude_values(prefixes))
            menu.addAction(act_ex_prefixes)

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def on_search(self):
        user_data = windows_edge_user_data_dir()
        if user_data is None:
            QMessageBox.warning(self, "Edge not found", "Could not find Edge user data directory via LOCALAPPDATA.")
            return
        profile = self.profile.currentText() or "Default"
        history_db = Path(user_data) / profile / "History"
        if not history_db.exists():
            QMessageBox.warning(self, "History not found", f"History DB not found: {history_db}")
            return

        ds = self.dateStart.date().toPython()
        de = self.dateEnd.date().toPython()
        ts = self.timeStart.time().toPython()
        te = self.timeEnd.time().toPython()

        start_dt = datetime.combine(ds, ts)
        end_dt = datetime.combine(de, te)
        if end_dt < start_dt:
            QMessageBox.warning(self, "Invalid range", "End datetime is before start datetime.")
            return

        try:
            rows = query_history(
                history_db=history_db,
                start_dt=start_dt,
                end_dt=end_dt,
                excludes=self.excludes(),
                limit=int(self.limit.value()),
                typed_only=bool(self.typedOnly.isChecked()),
            )
        except Exception as e:
            QMessageBox.critical(self, "Query failed", str(e))
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


def main() -> int:
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
