"""BatchPanel — Multi-file batch conversion with unified template selection."""

import os
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QPushButton, QFileDialog, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QLineEdit,
)
from PySide6.QtCore import Signal, Qt, Slot
from PySide6.QtGui import QColor

from src.config.settings import AppSettings
from src.core.template_manager import scan_templates, TemplateInfo
from src.core.workers import BatchConversionWorker

log = logging.getLogger(__name__)


class BatchPanel(QWidget):
    """Tab 4: Batch processing of multiple PDFs."""

    def __init__(self, settings: AppSettings):
        super().__init__()
        self.settings = settings
        self._files: list[str] = []
        self._templates: list[TemplateInfo] = []
        self._worker: BatchConversionWorker | None = None

        self._setup_ui()
        self._refresh_templates()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Top: file list + add/remove buttons
        file_group = QGroupBox("PDF Files")
        file_layout = QVBoxLayout(file_group)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add PDFs...")
        add_btn.clicked.connect(self._add_files)
        btn_row.addWidget(add_btn)

        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self._remove_selected)
        btn_row.addWidget(remove_btn)

        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self._clear_files)
        btn_row.addWidget(clear_btn)

        btn_row.addStretch()
        file_layout.addLayout(btn_row)

        self.file_table = QTableWidget()
        self.file_table.setColumnCount(3)
        self.file_table.setHorizontalHeaderLabels(["File", "Status", "Output"])
        self.file_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.file_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.file_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.file_table.setAlternatingRowColors(True)
        self.file_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        file_layout.addWidget(self.file_table)

        layout.addWidget(file_group, 1)

        # Template + output selection
        config_row = QHBoxLayout()

        config_row.addWidget(QLabel("Template:"))
        self.template_combo = QComboBox()
        self.template_combo.setMinimumWidth(250)
        config_row.addWidget(self.template_combo)

        config_row.addSpacing(16)

        config_row.addWidget(QLabel("Output Dir:"))
        self.output_edit = QLineEdit(self.settings.output_dir())
        self.output_edit.setReadOnly(True)
        config_row.addWidget(self.output_edit)

        change_out_btn = QPushButton("Change")
        change_out_btn.clicked.connect(self._change_output_dir)
        config_row.addWidget(change_out_btn)

        layout.addLayout(config_row)

        # Progress
        progress_row = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Idle")
        progress_row.addWidget(self.progress_bar, 1)

        self.start_btn = QPushButton("Start Batch")
        self.start_btn.setObjectName("primaryButton")
        self.start_btn.setMinimumHeight(36)
        self.start_btn.clicked.connect(self._start_batch)
        progress_row.addWidget(self.start_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._cancel_batch)
        progress_row.addWidget(self.cancel_btn)

        layout.addLayout(progress_row)

    def _refresh_templates(self):
        self._templates = scan_templates(self.settings.template_dir())
        self.template_combo.clear()
        for tmpl in self._templates:
            self.template_combo.addItem(tmpl.display_name, tmpl.path)

    def _add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select PDF Files", "", "PDF Files (*.pdf)"
        )
        for p in paths:
            if p not in self._files:
                self._files.append(p)
        self._update_file_table()

    def _remove_selected(self):
        rows = sorted(set(idx.row() for idx in self.file_table.selectedIndexes()), reverse=True)
        for r in rows:
            if 0 <= r < len(self._files):
                del self._files[r]
        self._update_file_table()

    def _clear_files(self):
        self._files.clear()
        self._update_file_table()

    def _update_file_table(self):
        self.file_table.setRowCount(len(self._files))
        for i, path in enumerate(self._files):
            self.file_table.setItem(i, 0, QTableWidgetItem(os.path.basename(path)))
            self.file_table.setItem(i, 1, QTableWidgetItem("Pending"))
            self.file_table.setItem(i, 2, QTableWidgetItem(""))

    def _change_output_dir(self):
        path = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if path:
            self.output_edit.setText(path)
            self.settings.set_output_dir(path)

    def _start_batch(self):
        if not self._files:
            return

        template_path = self.template_combo.currentData()
        if not template_path:
            return

        out_dir = self.output_edit.text()
        os.makedirs(out_dir, exist_ok=True)

        # Build file list with output paths
        file_list = []
        for pdf_path in self._files:
            base = os.path.splitext(os.path.basename(pdf_path))[0]
            ext = os.path.splitext(template_path)[1]
            output_path = os.path.join(out_dir, f"{base}_filled{ext}")
            file_list.append((pdf_path, template_path, output_path))

        self.progress_bar.setMaximum(len(file_list))
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("%v / %m files")
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)

        self._worker = BatchConversionWorker(file_list)
        self._worker.file_started.connect(self._on_file_started)
        self._worker.file_finished.connect(self._on_file_finished)
        self._worker.batch_finished.connect(self._on_batch_finished)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.start()

    def _cancel_batch(self):
        if self._worker:
            self._worker.cancel()
            self.cancel_btn.setEnabled(False)

    @Slot(int, str)
    def _on_file_started(self, idx: int, filename: str):
        if 0 <= idx < self.file_table.rowCount():
            item = self.file_table.item(idx, 1)
            if item:
                item.setText("Processing...")
                item.setForeground(QColor("#007AFF"))

    @Slot(int, object)
    def _on_file_finished(self, idx: int, result):
        self.progress_bar.setValue(idx + 1)
        if 0 <= idx < self.file_table.rowCount():
            status_item = self.file_table.item(idx, 1)
            output_item = self.file_table.item(idx, 2)
            if result.success:
                status_item.setText("Done")
                status_item.setForeground(QColor("#34C759"))
                output_item.setText(os.path.basename(result.output_path))
            else:
                status_item.setText("Failed")
                status_item.setForeground(QColor("#FF3B30"))
                output_item.setText(result.error or "Unknown error")

    @Slot(list)
    def _on_batch_finished(self, results: list):
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        success = sum(1 for r in results if r.success)
        self.progress_bar.setFormat(f"Done — {success}/{len(results)} succeeded")

    @Slot(int, str)
    def _on_error(self, idx: int, error: str):
        if 0 <= idx < self.file_table.rowCount():
            item = self.file_table.item(idx, 1)
            if item:
                item.setText("Error")
                item.setForeground(QColor("#FF3B30"))
