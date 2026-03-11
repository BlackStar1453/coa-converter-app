"""Trial period banner and expiration dialog widgets."""

import math
from PySide6.QtWidgets import (
    QWidget, QLabel, QHBoxLayout, QDialog, QVBoxLayout, QPushButton,
    QApplication,
)
from PySide6.QtCore import Qt


class TrialBanner(QWidget):
    """Horizontal banner showing remaining trial days."""

    def __init__(self, remaining_days: float, parent=None):
        super().__init__(parent)
        days = max(1, math.ceil(remaining_days))
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel(
            f"  测试版本 — 剩余 {days} 天 | 到期后请联系开发者获取正式版本"
        )
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(
            "background-color: #FFA726; color: #333; font-weight: bold;"
            "padding: 6px; border-radius: 0px; font-size: 13px;"
        )
        layout.addWidget(label)


class TrialExpiredDialog(QDialog):
    """Modal dialog blocking the application after trial expiration."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("试用期已结束")
        self.setModal(True)
        self.setFixedSize(420, 220)
        self.setWindowFlags(
            Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(32, 28, 32, 28)

        title = QLabel("试用期已结束")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #D32F2F;")
        layout.addWidget(title)

        msg = QLabel("此测试版本已过期。请联系开发者获取正式版本。")
        msg.setAlignment(Qt.AlignCenter)
        msg.setWordWrap(True)
        msg.setStyleSheet("font-size: 14px;")
        layout.addWidget(msg)

        email = QLabel("Email: developer@example.com")
        email.setAlignment(Qt.AlignCenter)
        email.setStyleSheet("font-size: 13px; color: #555;")
        layout.addWidget(email)

        btn = QPushButton("退出")
        btn.setFixedWidth(120)
        btn.setStyleSheet(
            "QPushButton { background-color: #D32F2F; color: white;"
            "font-size: 14px; padding: 8px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #B71C1C; }"
        )
        btn.clicked.connect(self._quit)
        layout.addWidget(btn, alignment=Qt.AlignCenter)

    def _quit(self):
        QApplication.instance().quit()

    def closeEvent(self, event):
        """Prevent closing the dialog without clicking Quit."""
        event.ignore()
        self._quit()
