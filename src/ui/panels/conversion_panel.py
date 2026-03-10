"""ConversionPanel — 6-step pipeline progress display with real-time logging."""

import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QProgressBar, QGroupBox, QPushButton, QFrame,
)
from PySide6.QtCore import Signal, Qt, Slot
from PySide6.QtGui import QColor, QTextCharFormat, QFont

from src.core.log_handler import QtLogHandler
from src.core.workers import ConversionWorker
from src.core.converter import ConversionResult

log = logging.getLogger(__name__)

# Step status indicators
PENDING = "\u2B58"    # ⬘ (empty circle)
RUNNING = "\u25B6"    # ▶ (play)
DONE    = "\u2714"    # ✔ (check)
FAILED  = "\u2718"    # ✘ (cross)
SKIPPED = "\u2500"    # ─ (dash)


class StepIndicator(QFrame):
    """A single pipeline step with icon + label + status."""

    def __init__(self, step_name: str):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        self.icon_label = QLabel(PENDING)
        self.icon_label.setFixedWidth(24)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.icon_label)

        self.name_label = QLabel(step_name)
        self.name_label.setStyleSheet("font-size: 13px;")
        layout.addWidget(self.name_label, 1)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #888; font-size: 11px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.status_label)

    def set_running(self):
        self.icon_label.setText(RUNNING)
        self.icon_label.setStyleSheet("color: #007AFF; font-size: 16px;")
        self.status_label.setText("Running...")
        self.name_label.setStyleSheet("font-size: 13px; font-weight: bold;")

    def set_done(self, detail: str = ""):
        self.icon_label.setText(DONE)
        self.icon_label.setStyleSheet("color: #34C759; font-size: 16px;")
        self.status_label.setText(detail or "Done")
        self.name_label.setStyleSheet("font-size: 13px;")

    def set_failed(self, detail: str = ""):
        self.icon_label.setText(FAILED)
        self.icon_label.setStyleSheet("color: #FF3B30; font-size: 16px;")
        self.status_label.setText(detail or "Failed")
        self.name_label.setStyleSheet("font-size: 13px; color: #FF3B30;")

    def set_skipped(self):
        self.icon_label.setText(SKIPPED)
        self.icon_label.setStyleSheet("color: #888; font-size: 16px;")
        self.status_label.setText("Skipped")

    def reset(self):
        self.icon_label.setText(PENDING)
        self.icon_label.setStyleSheet("color: #888; font-size: 16px;")
        self.status_label.setText("")
        self.name_label.setStyleSheet("font-size: 13px;")


class ConversionPanel(QWidget):
    """Tab 2: Pipeline steps + live log viewer."""
    pipeline_complete = Signal(object)  # ConversionResult or list[ConversionResult]

    def __init__(self, qt_log_handler: QtLogHandler):
        super().__init__()
        self._worker: ConversionWorker | None = None
        self._qt_log_handler = qt_log_handler

        # Multi-template queue
        self._task_queue: list[tuple[str, str, str]] = []  # (pdf, template, output)
        self._task_index: int = 0
        self._results: list = []

        self._setup_ui()
        self._connect_log()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Pipeline progress
        pipeline_group = QGroupBox("Conversion Pipeline")
        pipeline_layout = QVBoxLayout(pipeline_group)

        # Multi-template progress label
        self.template_progress_label = QLabel("")
        self.template_progress_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #007AFF;")
        self.template_progress_label.setVisible(False)
        pipeline_layout.addWidget(self.template_progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(len(ConversionWorker.STEPS))
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%v / %m steps")
        pipeline_layout.addWidget(self.progress_bar)

        self.step_indicators: list[StepIndicator] = []
        for step_name in ConversionWorker.STEPS:
            indicator = StepIndicator(step_name)
            self.step_indicators.append(indicator)
            pipeline_layout.addWidget(indicator)

        layout.addWidget(pipeline_group)

        # Log viewer
        log_group = QGroupBox("Log Output")
        log_layout = QVBoxLayout(log_group)

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFont(QFont("Menlo", 11))
        self.log_view.setMinimumHeight(180)
        log_layout.addWidget(self.log_view)

        # Clear + Cancel buttons
        btn_row = QHBoxLayout()
        self.clear_btn = QPushButton("Clear Log")
        self.clear_btn.clicked.connect(self.log_view.clear)
        btn_row.addWidget(self.clear_btn)

        btn_row.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._on_cancel)
        btn_row.addWidget(self.cancel_btn)

        log_layout.addLayout(btn_row)
        layout.addWidget(log_group)

    def _connect_log(self):
        self._qt_log_handler.signaler.log_record.connect(self._append_log)

    @Slot(str, str)
    def _append_log(self, level: str, message: str):
        color_map = {
            "DEBUG": "#888888",
            "INFO": "#333333",
            "WARNING": "#FF9500",
            "ERROR": "#FF3B30",
            "CRITICAL": "#FF3B30",
        }
        color = color_map.get(level, "#333333")
        self.log_view.append(f'<span style="color:{color}">{message}</span>')

    def start_multi_pipeline(self, pdf_path: str, template_paths: list[str], output_dir: str):
        """Start conversion for one or more templates sequentially."""
        import os

        self._task_queue.clear()
        self._results.clear()
        self._task_index = 0

        base = os.path.splitext(os.path.basename(pdf_path))[0]
        for tp in template_paths:
            ext = os.path.splitext(tp)[1]
            tmpl_name = os.path.splitext(os.path.basename(tp))[0]
            # Include template name in output to avoid collisions
            if len(template_paths) > 1:
                out = os.path.join(output_dir, f"{base}_{tmpl_name}_filled{ext}")
            else:
                out = os.path.join(output_dir, f"{base}_filled{ext}")
            self._task_queue.append((pdf_path, tp, out))

        # Reset UI
        self.log_view.clear()
        self.cancel_btn.setEnabled(True)

        if len(self._task_queue) > 1:
            self.template_progress_label.setVisible(True)
        else:
            self.template_progress_label.setVisible(False)

        self._start_next_task()

    def _start_next_task(self):
        """Start the next template conversion in the queue."""
        import os

        if self._task_index >= len(self._task_queue):
            # All done
            self.template_progress_label.setVisible(False)
            self.cancel_btn.setEnabled(False)
            self.pipeline_complete.emit(list(self._results))
            return

        pdf_path, template_path, output_path = self._task_queue[self._task_index]
        total = len(self._task_queue)
        tmpl_name = os.path.basename(template_path)

        if total > 1:
            self.template_progress_label.setText(
                f"Template {self._task_index + 1}/{total}: {tmpl_name}"
            )

        # Reset step indicators
        self.progress_bar.setValue(0)
        for indicator in self.step_indicators:
            indicator.reset()

        # Create and start worker
        self._worker = ConversionWorker(pdf_path, template_path, output_path)
        self._worker.step_started.connect(self._on_step_started)
        self._worker.step_finished.connect(self._on_step_finished)
        self._worker.pipeline_finished.connect(self._on_single_pipeline_finished)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.start()

    def start_pipeline(self, pdf_path: str, template_path: str, output_path: str):
        """Start the conversion worker (single template, legacy compat)."""
        self._task_queue = [(pdf_path, template_path, output_path)]
        self._results.clear()
        self._task_index = 0
        self.template_progress_label.setVisible(False)

        # Reset UI
        self.progress_bar.setValue(0)
        for indicator in self.step_indicators:
            indicator.reset()
        self.log_view.clear()
        self.cancel_btn.setEnabled(True)

        # Create and start worker
        self._worker = ConversionWorker(pdf_path, template_path, output_path)
        self._worker.step_started.connect(self._on_step_started)
        self._worker.step_finished.connect(self._on_step_finished)
        self._worker.pipeline_finished.connect(self._on_single_pipeline_finished)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.start()

    @Slot(int, str)
    def _on_step_started(self, idx: int, desc: str):
        if 0 <= idx < len(self.step_indicators):
            self.step_indicators[idx].set_running()

    @Slot(int, object)
    def _on_step_finished(self, idx: int, data: dict):
        if 0 <= idx < len(self.step_indicators):
            if isinstance(data, dict) and data.get("skipped"):
                self.step_indicators[idx].set_skipped()
            else:
                detail = ""
                if isinstance(data, dict):
                    if "accuracy" in data:
                        detail = f"{data['accuracy']*100:.0f}% accuracy"
                    elif "warnings" in data:
                        wc = len(data["warnings"])
                        detail = f"{wc} warning(s)" if wc else "OK"
                    elif "type" in data:
                        detail = data["type"]
                self.step_indicators[idx].set_done(detail)

            self.progress_bar.setValue(idx + 1)

    @Slot(object)
    def _on_single_pipeline_finished(self, result: ConversionResult):
        """One template conversion finished; proceed to next or emit all results."""
        self._results.append(result)

        if result.success:
            self.progress_bar.setFormat("Complete")
        else:
            self.progress_bar.setFormat("Failed")

        # Move to next task
        self._task_index += 1
        self._start_next_task()

    @Slot(str)
    def _on_error(self, error_msg: str):
        # Mark current running step as failed
        for indicator in self.step_indicators:
            if indicator.icon_label.text() == RUNNING:
                indicator.set_failed(error_msg[:50])
                break

    def _on_cancel(self):
        if self._worker:
            self._worker.cancel()
            self.cancel_btn.setEnabled(False)
            log.info("[ConversionPanel] Cancellation requested.")
