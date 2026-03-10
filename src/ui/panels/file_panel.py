"""FilePanel — PDF selection, template selection, output path configuration."""

import os
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QPushButton, QFileDialog, QCheckBox,
    QLineEdit, QScrollArea, QFrame,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent

from src.config.settings import AppSettings
from src.core.template_manager import scan_templates, TemplateInfo

log = logging.getLogger(__name__)


class DropZone(QFrame):
    """A drag-and-drop zone for PDF files."""
    file_dropped = Signal(str)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setMinimumHeight(120)
        self.setObjectName("dropZone")
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Sunken)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.icon_label = QLabel("PDF")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #888;")
        layout.addWidget(self.icon_label)

        self.text_label = QLabel("Drag & drop PDF here\nor click Browse")
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setStyleSheet("color: #666;")
        layout.addWidget(self.text_label)

        self.file_label = QLabel("")
        self.file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.file_label.setStyleSheet("color: #007AFF; font-weight: bold;")
        self.file_label.setWordWrap(True)
        layout.addWidget(self.file_label)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith(".pdf"):
                    event.acceptProposedAction()
                    self.setStyleSheet("#dropZone { border: 2px dashed #007AFF; background: #E8F0FE; }")
                    return
        event.ignore()

    def dragLeaveEvent(self, event):
        self.setStyleSheet("")

    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet("")
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith(".pdf"):
                self.set_file(path)
                self.file_dropped.emit(path)
                return

    def set_file(self, path: str):
        self.file_label.setText(os.path.basename(path))
        self.text_label.setText("Selected:")


class FilePanel(QWidget):
    """Tab 1: PDF file selection + template selection + output path."""
    start_conversion = Signal(str, list, str)  # (pdf_path, template_paths, output_dir)

    def __init__(self, settings: AppSettings):
        super().__init__()
        self.settings = settings
        self._pdf_path = ""
        self._selected_templates: list[str] = []
        self._templates: list[TemplateInfo] = []
        self._template_buttons: list[QCheckBox] = []

        self._setup_ui()
        self.refresh_templates()

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(16)

        # --- Left: PDF selection ---
        left_group = QGroupBox("PDF Source File")
        left_layout = QVBoxLayout(left_group)

        self.drop_zone = DropZone()
        self.drop_zone.file_dropped.connect(self._on_pdf_selected)
        left_layout.addWidget(self.drop_zone)

        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self._browse_pdf)
        left_layout.addWidget(self.browse_btn)

        left_layout.addSpacing(16)

        # Output directory
        out_label = QLabel("Output Directory:")
        left_layout.addWidget(out_label)

        out_row = QHBoxLayout()
        self.output_edit = QLineEdit(self.settings.output_dir())
        self.output_edit.setReadOnly(True)
        out_row.addWidget(self.output_edit)

        change_btn = QPushButton("Change")
        change_btn.clicked.connect(self._browse_output_dir)
        out_row.addWidget(change_btn)
        left_layout.addLayout(out_row)

        left_layout.addStretch()
        main_layout.addWidget(left_group, 1)

        # --- Right: Template selection ---
        right_group = QGroupBox("Template Selection")
        right_layout = QVBoxLayout(right_group)

        # Scrollable template list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.template_container = QWidget()
        self.template_list_layout = QVBoxLayout(self.template_container)
        self.template_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll.setWidget(self.template_container)
        right_layout.addWidget(scroll)
        main_layout.addWidget(right_group, 1)

        # --- Bottom: Start button ---
        bottom = QHBoxLayout()
        bottom.addStretch()

        self.start_btn = QPushButton("Start Conversion >>")
        self.start_btn.setObjectName("primaryButton")
        self.start_btn.setMinimumHeight(40)
        self.start_btn.setMinimumWidth(180)
        self.start_btn.setEnabled(False)
        self.start_btn.clicked.connect(self._on_start)
        bottom.addWidget(self.start_btn)

        # We need to wrap the main layout in a vertical layout
        # to add the bottom row
        wrapper = QVBoxLayout()
        row_widget = QWidget()
        row_widget.setLayout(main_layout)
        wrapper.addWidget(row_widget, 1)
        wrapper.addLayout(bottom)

        # Reset self layout
        # Clear existing layout
        if self.layout():
            QWidget().setLayout(self.layout())
        self.setLayout(wrapper)

    def refresh_templates(self):
        """Rescan template directory and rebuild checkboxes."""
        # Clear existing
        for btn in self._template_buttons:
            btn.deleteLater()
        self._template_buttons.clear()
        self._selected_templates.clear()

        # Clear layout
        while self.template_list_layout.count():
            item = self.template_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Scan
        self._templates = scan_templates(self.settings.template_dir())

        current_category = ""
        for i, tmpl in enumerate(self._templates):
            if tmpl.category != current_category:
                current_category = tmpl.category
                cat_label = QLabel(f"— {current_category} —")
                cat_label.setStyleSheet("color: #888; font-size: 11px; margin-top: 8px;")
                self.template_list_layout.addWidget(cat_label)

            cb = QCheckBox(tmpl.display_name)
            cb.setProperty("template_index", i)
            cb.stateChanged.connect(self._on_template_toggled)
            self.template_list_layout.addWidget(cb)
            self._template_buttons.append(cb)

        self.template_list_layout.addStretch()
        self._update_start_enabled()

    def _browse_pdf(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select PDF", "", "PDF Files (*.pdf)"
        )
        if path:
            self._on_pdf_selected(path)

    def _on_pdf_selected(self, path: str):
        self._pdf_path = path
        self.drop_zone.set_file(path)
        log.info("[FilePanel] PDF selected: %s", path)
        self._update_start_enabled()

    def _on_template_toggled(self, state: int):
        """Rebuild selected templates list from checked checkboxes."""
        self._selected_templates.clear()
        for btn in self._template_buttons:
            if btn.isChecked():
                idx = btn.property("template_index")
                if idx is not None and 0 <= idx < len(self._templates):
                    self._selected_templates.append(self._templates[idx].path)
        log.info("[FilePanel] Selected %d template(s)", len(self._selected_templates))
        self._update_start_enabled()

    def _browse_output_dir(self):
        path = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if path:
            self.output_edit.setText(path)
            self.settings.set_output_dir(path)

    def _update_start_enabled(self):
        self.start_btn.setEnabled(bool(self._pdf_path and self._selected_templates))

    def _on_start(self):
        if not self._pdf_path or not self._selected_templates:
            return

        out_dir = self.output_edit.text()
        os.makedirs(out_dir, exist_ok=True)

        log.info(
            "[FilePanel] Starting: %s + %d template(s) → %s",
            self._pdf_path, len(self._selected_templates), out_dir,
        )
        self.start_conversion.emit(self._pdf_path, list(self._selected_templates), out_dir)
