from PyQt6.QtCore import QObject, pyqtSignal

class SignalBus(QObject):
    # This signal tells every widget to re-fetch their data from the DB
    refresh_requested = pyqtSignal()

# Singleton instance
global_signal = SignalBus()