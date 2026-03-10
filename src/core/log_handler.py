"""Bridge Python logging to Qt signals for real-time log display."""

import logging
from PySide6.QtCore import QObject, Signal


class QtLogSignaler(QObject):
    """Emits a signal for each log record."""
    log_record = Signal(str, str)  # (level_name, formatted_message)


class QtLogHandler(logging.Handler):
    """Logging handler that forwards records to a Qt signal.

    Usage:
        handler = QtLogHandler()
        handler.signaler.log_record.connect(some_widget.append_log)
        logging.getLogger().addHandler(handler)
    """

    def __init__(self, level=logging.DEBUG):
        super().__init__(level)
        self.signaler = QtLogSignaler()
        self.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S"))

    def emit(self, record: logging.LogRecord):
        try:
            msg = self.format(record)
            self.signaler.log_record.emit(record.levelname, msg)
        except Exception:
            self.handleError(record)
