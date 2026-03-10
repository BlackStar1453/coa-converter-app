"""COA Converter Desktop Application — Entry Point."""

import sys
import os
import logging

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from src.ui.main_window import MainWindow
from src.core.log_handler import QtLogHandler


def setup_logging(qt_handler: QtLogHandler):
    """Configure root logger with console + Qt handler."""
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # Console handler
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", "%H:%M:%S"))
    root.addHandler(console)

    # Qt handler (bridges to UI)
    root.addHandler(qt_handler)


def main():
    # High-DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("COA Converter")
    app.setOrganizationName("COAConverter")

    # Load QSS theme
    qss_path = os.path.join(os.path.dirname(__file__), "styles", "theme.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r") as f:
            app.setStyleSheet(f.read())

    # App icon (platform-aware extension)
    import platform
    icon_ext = ".icns" if platform.system() == "Darwin" else ".ico"
    icon_path = os.path.join(os.path.dirname(__file__), "..", "assets", f"icon{icon_ext}")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Setup logging with Qt bridge
    qt_log_handler = QtLogHandler()
    setup_logging(qt_log_handler)

    # Create and show main window
    window = MainWindow(qt_log_handler)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
