from PyQt6.QtWidgets import QMainWindow, QStackedWidget

from ui.component.styles import CAPITAL_ONE_STYLE
from ui.view.Login import Login
from ui.view.MainApp import MainApp

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WealthTrackers")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet(CAPITAL_ONE_STYLE)

        self.main_stack = QStackedWidget()
        self.setCentralWidget(self.main_stack)

        # entry point
        self.show_login()

    def show_login(self):
        self.login_view = Login(on_login_success=self.show_main_app)
        self.main_stack.addWidget(self.login_view)
        self.main_stack.setCurrentWidget(self.login_view)

    def show_main_app(self):
        self.app_view = MainApp(on_logout=self.show_login)
        self.main_stack.addWidget(self.app_view)
        self.main_stack.setCurrentWidget(self.app_view)