import sys
import os
import sqlite3

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon

from ui.MainWindow import MainWindow
from ui.component.styles import CAPITAL_ONE_STYLE

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def initialize_database():
    """Checks for the SQLite DB and creates it using the schema script if missing."""
    db_path = "WealthTrackersDB.sqlite"
    schema_path = resource_path(os.path.join("schema.sql"))

    if not os.path.exists(db_path):
        print(f"Database {db_path} not found. Initializing from {schema_path}...")

        if not os.path.exists(schema_path):
            print(f"CRITICAL ERROR: Schema script not found at {schema_path}")
            return False

        try:
            conn = sqlite3.connect(db_path)
            with open(schema_path, 'r') as f:
                schema_script = f.read()

            conn.executescript(schema_script)
            conn.commit()
            conn.close()

            print("Database initialized successfully.")
            return True
        except Exception as e:
            print(f"Database initialization failed: {e}")
            return False

    return True

if __name__ == '__main__':
    # 1. Initialize DB
    if not initialize_database():
        app = QApplication(sys.argv)
        QMessageBox.critical(None, "Initialization Error",
                             "Could not initialize the database. Ensure schema.sql exists.")
        sys.exit(1)

    app = QApplication(sys.argv)

    # APPLY GLOBAL THEME
    app.setStyleSheet(CAPITAL_ONE_STYLE)

    icon_path = resource_path("icon.webp")

    if os.path.exists(icon_path):
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)  # Sets the icon for taskbar
    else:
        print(f"Warning: Icon not found at {icon_path}")

    window = MainWindow()

    if os.path.exists(icon_path):
        window.setWindowIcon(QIcon(icon_path))  # Sets the icon for window top bar

    window.show()
    sys.exit(app.exec())