import json
from typing import List
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QSortFilterProxyModel, QTimer
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QComboBox,
    QTableView, QSplitter, QTextEdit, QFormLayout, QDialog
)

from models.result import FileResult

COLUMNS = [
    ("Path", "path"),
    ("Status", "status"),
    ("Reason", "reason"),
    ("Template", "template"),
]

STATUS_ORDER = ["Error", "Replaced", "Created", "Unchanged", "Skipped"]


# ----- Model -----
class ResultsTableModel(QAbstractTableModel):
    def __init__(self, rows: List[FileResult]):
        super().__init__()
        self._rows = rows

    def rowCount(self, parent=QModelIndex()):
        return len(self._rows)

    def columnCount(self, parent=QModelIndex()):
        return len(COLUMNS)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row = self._rows[index.row()]
        col_name = COLUMNS[index.column()][1]

        if role == Qt.DisplayRole:
            val = getattr(row, col_name)
            if isinstance(val, dict):
                return json.dumps(val, ensure_ascii=False)
            return str(val)

        if role == Qt.ForegroundRole:
            if row.status == "Error":
                return QColor("#d73a49")
            if row.status == "Replaced":
                return QColor("#22863a")
            if row.status == "Created":
                return QColor("#0366d6")
            if row.status == "Skipped":
                return QColor("#6a737d")

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return COLUMNS[section][0]
        return str(section + 1)

    def row(self, r: int) -> FileResult:
        return self._rows[r]

    def setRows(self, rows: List[FileResult]):
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()


# ----- Filtering/Sorting -----
class ResultsFilterProxy(QSortFilterProxyModel):
    def __init__(self):
        super().__init__()
        self._status_filter = "All"
        self._search_text = ""

    def setStatusFilter(self, status: str):
        self._status_filter = status
        self.invalidateFilter()

    def setSearchText(self, text: str):
        self._search_text = text.lower()
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        model: ResultsTableModel = self.sourceModel()
        row = model.row(source_row)

        if self._status_filter != "All" and row.status != self._status_filter:
            return False

        if self._search_text:
            hay = f"{row.path} {row.status} {row.reason} {row.template}".lower()
            if self._search_text not in hay:
                return False

        return True

    def lessThan(self, left, right):
        col_name = COLUMNS[left.column()][1]
        L = self.sourceModel().row(left.row())
        R = self.sourceModel().row(right.row())

        if col_name == "status":
            def rank(s):
                try:
                    return STATUS_ORDER.index(s)
                except ValueError:
                    return len(STATUS_ORDER)

            return rank(L.status) < rank(R.status)

        if col_name in ("bytes_written", "duration_ms"):
            return getattr(L, col_name) < getattr(R, col_name)

        return str(getattr(L, col_name)) < str(getattr(R, col_name))


# ----- UI -----
class DetailPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.form = QFormLayout(self)
        self.lbl_path = QLabel("-")
        self.lbl_status = QLabel("-")
        self.lbl_reason = QLabel("-")
        self.lbl_template = QLabel("-")
        self.lbl_bytes = QLabel("-")
        self.lbl_duration = QLabel("-")
        self.txt_vars = QTextEdit()
        self.txt_vars.setReadOnly(True)
        self.txt_vars.setLineWrapMode(QTextEdit.NoWrap)

        self.form.addRow("Path", self.lbl_path)
        self.form.addRow("Status", self.lbl_status)
        self.form.addRow("Reason", self.lbl_reason)
        self.form.addRow("Template", self.lbl_template)
        self.form.addRow("Variables", self.txt_vars)

    def set_data(self, item: FileResult | None):
        if not item:
            self.lbl_path.setText("-")
            self.lbl_status.setText("-")
            self.lbl_reason.setText("-")
            self.lbl_template.setText("-")
            self.txt_vars.setPlainText("")
            return
        self.lbl_path.setText(item.path)
        self.lbl_status.setText(item.status)
        self.lbl_reason.setText(item.reason)
        self.lbl_template.setText(item.template)
        self.txt_vars.setPlainText(json.dumps(item.variables_used, indent=2, ensure_ascii=False))


class SummaryBar(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.total = QLabel("Total: 0")
        self.replaced = QLabel("Replaced: 0")
        self.created = QLabel("Created: 0")
        self.unchanged = QLabel("Unchanged: 0")
        self.skipped = QLabel("Skipped: 0")
        self.error = QLabel("Error: 0")
        layout.addWidget(self.total)
        layout.addWidget(self.replaced)
        layout.addWidget(self.created)
        layout.addWidget(self.unchanged)
        layout.addWidget(self.skipped)
        layout.addWidget(self.error)
        layout.addStretch()

    def update_counts(self, rows: List[FileResult]):
        cnts = {"Total": len(rows), "Replaced": 0, "Created": 0, "Unchanged": 0, "Skipped": 0, "Error": 0}
        for r in rows:
            if r.status in cnts:
                cnts[r.status] += 1
        self.total.setText(f"Total: {cnts['Total']}")
        self.replaced.setText(f"Replaced: {cnts['Replaced']}")
        self.created.setText(f"Created: {cnts['Created']}")
        self.unchanged.setText(f"Unchanged: {cnts['Unchanged']}")
        self.skipped.setText(f"Skipped: {cnts['Skipped']}")
        self.error.setText(f"Error: {cnts['Error']}")


class FileResultWindow(QDialog):
    def __init__(self, rows: List[FileResult]):
        super().__init__()
        self.setWindowTitle("Template Apply Results")
        self.resize(1200, 720)

        self.model = ResultsTableModel(rows)
        self.proxy = ResultsFilterProxy()
        self.proxy.setSourceModel(self.model)

        # Top controls
        top = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search path/status/reason/template...")
        self.status = QComboBox()
        self.status.addItems(["All"] + STATUS_ORDER + ["Replaced", "Created", "Unchanged", "Skipped"])
        # deduplicate while preserving order
        seen, items = set(), []
        for i in range(self.status.count()):
            s = self.status.itemText(i)
            if s not in seen:
                items.append(s);
                seen.add(s)
        self.status.clear();
        self.status.addItems(items)

        top.addWidget(QLabel("Filter"))
        top.addWidget(self.search, 1)
        top.addWidget(QLabel("Status"))
        top.addWidget(self.status)
        top.addStretch()

        # Center split: table + details
        self.table = QTableView()
        self.table.setModel(self.proxy)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setWordWrap(False)
        self.table.setEditTriggers(QTableView.NoEditTriggers)
        self.table.setColumnWidth(0, 450)

        self.details = DetailPanel()

        split = QSplitter()
        split.addWidget(self.table)
        split.addWidget(self.details)
        split.setSizes([800, 400])

        # Bottom summary
        self.summary = SummaryBar()
        self.summary.update_counts(rows)

        root = QVBoxLayout(self)
        root.addLayout(top)
        root.addWidget(split, 1)
        root.addWidget(self.summary)

        # Signals
        self.search.textChanged.connect(self.on_search)
        self.status.currentTextChanged.connect(self.on_status_change)
        self.table.selectionModel().currentRowChanged.connect(self.on_row_changed)

        # Select first row initially
        QTimer.singleShot(0, self.select_first)

    def select_first(self):
        if self.proxy.rowCount() > 0:
            self.table.selectRow(0)
            self.on_row_changed(self.proxy.index(0, 0), QModelIndex())

    def on_search(self, text: str):
        self.proxy.setSearchText(text)

    def on_status_change(self, status: str):
        self.proxy.setStatusFilter(status)

    def current_item(self) -> FileResult | None:
        idx = self.table.currentIndex()
        if not idx.isValid():
            return None
        src = self.proxy.mapToSource(idx)
        return self.model.row(src.row())

    def on_row_changed(self, current: QModelIndex, _prev: QModelIndex):
        self.details.set_data(self.current_item())
