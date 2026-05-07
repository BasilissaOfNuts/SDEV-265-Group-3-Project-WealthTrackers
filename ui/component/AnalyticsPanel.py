import sqlite3

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QComboBox, QLineEdit, QPushButton, QDateEdit, QCompleter)
from PyQt6.QtCore import Qt, QDate, QStringListModel

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from core.transaction.TransactionRepository import TransactionRepository
from core.account.AccountRepository import AccountRepository
from core.analytics.AnalyticsProcessor import AnalyticsProcessor
from core.authentication.UserSession import UserSession
from core.visualizer.BarGraphVisualizer import BarGraphVisualizer
from core.visualizer.LineGraphVisualizer import LineGraphVisualizer
from core.visualizer.PieChartVisualizer import PieChartVisualizer

class AnalyticsPanel(QWidget):
    def __init__(self, account_id=None):
        super().__init__()
        self.account_id = account_id
        self.session = UserSession()

        # Repositories and Processor
        self.txn_repo = TransactionRepository("WealthTrackersDB.sqlite")
        self.acc_repo = AccountRepository("WealthTrackersDB.sqlite")
        self.processor = AnalyticsProcessor(self.txn_repo, self.acc_repo)

        self.setup_ui()
        self.update_completer_data()  # Initial completer load
        self.handle_period_change()  # Sets default dates and triggers first render

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # --- Top Controls ---
        ctrl_layout1 = QHBoxLayout()

        self.chart_type = QComboBox()
        self.chart_type.addItems(["Bar Graph", "Line Chart", "Pie Chart"])
        self.chart_type.currentIndexChanged.connect(self.refresh_chart)
        ctrl_layout1.addWidget(self.chart_type)

        self.group_by = QComboBox()
        self.group_by.addItems(["Category", "Vendor"])
        self.group_by.currentIndexChanged.connect(self.on_group_by_changed)
        ctrl_layout1.addWidget(self.group_by)

        # Search box with Completer (Google-style Overlay)
        self.search_box = QLineEdit(placeholderText="Search...")
        self.search_box.textChanged.connect(self.refresh_chart)

        self.completer = QCompleter(self)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.search_box.setCompleter(self.completer)

        ctrl_layout1.addWidget(self.search_box)

        self.all_btn = QPushButton("ALL")
        self.all_btn.clicked.connect(self.clear_search)
        ctrl_layout1.addWidget(self.all_btn)

        layout.addLayout(ctrl_layout1)

        # --- Bottom Controls (Squished Dates) ---
        ctrl_layout2 = QHBoxLayout()
        ctrl_layout2.setSpacing(15)  # Spacing between segments

        self.period_combo = QComboBox()
        self.period_combo.addItems(["Daily", "Monthly", "Yearly"])
        self.period_combo.currentIndexChanged.connect(self.handle_period_change)
        ctrl_layout2.addWidget(self.period_combo)

        # Squish logic: Use a dedicated sub-layout for From/To
        date_input_layout = QHBoxLayout()
        date_input_layout.setSpacing(4)  # TIGHT SQUISH

        date_input_layout.addWidget(QLabel("From:"))
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.dateChanged.connect(self.refresh_chart)
        date_input_layout.addWidget(self.start_date)

        date_input_layout.addWidget(QLabel("To:"))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.dateChanged.connect(self.refresh_chart)
        date_input_layout.addWidget(self.end_date)

        ctrl_layout2.addLayout(date_input_layout)
        ctrl_layout2.addStretch()  # Pushes everything to the left

        layout.addLayout(ctrl_layout2)

        # --- Chart Canvas ---
        self.canvas_layout = QVBoxLayout()
        layout.addLayout(self.canvas_layout, stretch=1)

    def on_group_by_changed(self):
        self.update_completer_data()
        self.refresh_chart()

    def update_completer_data(self):
        """Fetches unique names from the DB to populate the search dropdown."""
        conn = sqlite3.connect(self.txn_repo.db_path)
        cursor = conn.cursor()

        if self.group_by.currentText() == "Vendor":
            cursor.execute("SELECT DISTINCT vendor_name FROM vendors")
        else:
            cursor.execute("SELECT DISTINCT category_name FROM categories")

        names = [row[0] for row in cursor.fetchall()]
        conn.close()

        # Create a proper string list model and set it
        model = QStringListModel()
        model.setStringList(names)
        self.completer.setModel(model)

    def clear_search(self):
        self.search_box.clear()
        self.refresh_chart()

    def handle_period_change(self):
        self.start_date.blockSignals(True)
        self.end_date.blockSignals(True)

        today = datetime.now()
        period = self.period_combo.currentText()

        if period == "Daily":
            start, end = today - timedelta(days=3), today + timedelta(days=3)
        elif period == "Monthly":
            start, end = today - relativedelta(months=3), today + relativedelta(months=3)
        else:
            start, end = today - relativedelta(years=3), today + relativedelta(years=3)

        self.start_date.setDate(QDate(start.year, start.month, start.day))
        self.end_date.setDate(QDate(end.year, end.month, end.day))

        self.start_date.blockSignals(False)
        self.end_date.blockSignals(False)
        self.refresh_chart()

    def refresh_chart(self):
        user_id = self.session.active_user_id
        if not user_id: return

        aggregated_data = self.processor.get_aggregated_data(
            user_id=user_id,
            account_id=self.account_id,
            start_date=datetime.combine(self.start_date.date().toPyDate(), datetime.min.time()),
            end_date=datetime.combine(self.end_date.date().toPyDate(), datetime.max.time()),
            group_by=self.group_by.currentText(),
            period_type=self.period_combo.currentText(),
            search_text=self.search_box.text()
        )

        c_type = self.chart_type.currentText()
        if c_type == "Bar Graph":
            visualizer = BarGraphVisualizer()
        elif c_type == "Line Chart":
            visualizer = LineGraphVisualizer()
        else:
            visualizer = PieChartVisualizer()

        fig = visualizer.render(aggregated_data, f"Analytics Trend ({self.group_by.currentText()})")

        while self.canvas_layout.count():
            item = self.canvas_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        canvas = FigureCanvas(fig)
        self.canvas_layout.addWidget(canvas)