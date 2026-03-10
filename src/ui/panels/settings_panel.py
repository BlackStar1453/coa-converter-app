"""SettingsPanel — Directories and supplier registry configuration."""

import os
import json
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QFileDialog,
    QTableWidget, QTableWidgetItem, QHeaderView,
)
from PySide6.QtCore import Signal

from src.config.settings import AppSettings

log = logging.getLogger(__name__)

# Status indicator style
_STYLE_OK = "color: #34C759; font-weight: bold;"
_STYLE_ERR = "color: #FF3B30; font-weight: bold;"


class SettingsPanel(QWidget):
    """Tab 5: Application settings."""
    settings_changed = Signal()

    def __init__(self, settings: AppSettings):
        super().__init__()
        self.settings = settings
        self._setup_ui()
        self._load_values()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # --- Directories ---
        paths_group = QGroupBox("Directories")
        paths_layout = QVBoxLayout(paths_group)

        # Converter directory
        conv_row = QHBoxLayout()
        conv_row.addWidget(QLabel("Converter Dir:"))
        self.converter_dir_edit = QLineEdit()
        self.converter_dir_edit.setReadOnly(True)
        conv_row.addWidget(self.converter_dir_edit)
        self.converter_dir_status = QLabel("")
        self.converter_dir_status.setFixedWidth(20)
        conv_row.addWidget(self.converter_dir_status)
        conv_browse = QPushButton("Browse")
        conv_browse.clicked.connect(self._browse_converter_dir)
        conv_row.addWidget(conv_browse)
        paths_layout.addLayout(conv_row)

        # Template directory
        tmpl_row = QHBoxLayout()
        tmpl_row.addWidget(QLabel("Template Dir:"))
        self.template_dir_edit = QLineEdit()
        self.template_dir_edit.setReadOnly(True)
        tmpl_row.addWidget(self.template_dir_edit)
        self.template_dir_status = QLabel("")
        self.template_dir_status.setFixedWidth(20)
        tmpl_row.addWidget(self.template_dir_status)
        tmpl_browse = QPushButton("Browse")
        tmpl_browse.clicked.connect(self._browse_template_dir)
        tmpl_row.addWidget(tmpl_browse)
        paths_layout.addLayout(tmpl_row)

        # Output directory
        out_row = QHBoxLayout()
        out_row.addWidget(QLabel("Output Dir:"))
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setReadOnly(True)
        out_row.addWidget(self.output_dir_edit)
        self.output_dir_status = QLabel("")
        self.output_dir_status.setFixedWidth(20)
        out_row.addWidget(self.output_dir_status)
        out_browse = QPushButton("Browse")
        out_browse.clicked.connect(self._browse_output_dir)
        out_row.addWidget(out_browse)
        paths_layout.addLayout(out_row)

        layout.addWidget(paths_group)

        # --- Supplier Registry ---
        supplier_group = QGroupBox("Supplier Registry")
        supplier_layout = QVBoxLayout(supplier_group)

        self.supplier_table = QTableWidget()
        self.supplier_table.setColumnCount(4)
        self.supplier_table.setHorizontalHeaderLabels(["ID", "Name", "Format", "Accuracy"])
        self.supplier_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.supplier_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.supplier_table.setAlternatingRowColors(True)
        supplier_layout.addWidget(self.supplier_table)

        refresh_btn = QPushButton("Refresh Registry")
        refresh_btn.clicked.connect(self._load_supplier_registry)
        supplier_layout.addWidget(refresh_btn)

        layout.addWidget(supplier_group)

        # --- Save button ---
        save_row = QHBoxLayout()
        save_row.addStretch()
        save_btn = QPushButton("Save Settings")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self._save_settings)
        save_row.addWidget(save_btn)
        layout.addLayout(save_row)

    def _load_values(self):
        self.converter_dir_edit.setText(self.settings.converter_dir())
        self.template_dir_edit.setText(self.settings.template_dir())
        self.output_dir_edit.setText(self.settings.output_dir())
        self._refresh_all_status()
        self._load_supplier_registry()

    def _refresh_all_status(self):
        """Update the exists/missing indicator for every directory."""
        self._update_dir_status(self.converter_dir_edit.text(), self.converter_dir_status)
        self._update_dir_status(self.template_dir_edit.text(), self.template_dir_status)
        self._update_dir_status(self.output_dir_edit.text(), self.output_dir_status)

    @staticmethod
    def _update_dir_status(path: str, label: QLabel):
        if path and os.path.isdir(path):
            label.setText("\u2714")
            label.setStyleSheet(_STYLE_OK)
            label.setToolTip("Directory exists")
        else:
            label.setText("\u2718")
            label.setStyleSheet(_STYLE_ERR)
            label.setToolTip("Directory not found")

    def _browse_template_dir(self):
        start = self.template_dir_edit.text()
        if not os.path.isdir(start):
            start = ""
        path = QFileDialog.getExistingDirectory(self, "Select Template Directory", start)
        if path:
            self.template_dir_edit.setText(path)
            self._update_dir_status(path, self.template_dir_status)

    def _browse_output_dir(self):
        start = self.output_dir_edit.text()
        if not os.path.isdir(start):
            start = ""
        path = QFileDialog.getExistingDirectory(self, "Select Output Directory", start)
        if path:
            self.output_dir_edit.setText(path)
            self._update_dir_status(path, self.output_dir_status)

    def _browse_converter_dir(self):
        start = self.converter_dir_edit.text()
        if not os.path.isdir(start):
            start = ""
        path = QFileDialog.getExistingDirectory(self, "Select COA Converter Directory", start)
        if path:
            self.converter_dir_edit.setText(path)
            self._update_dir_status(path, self.converter_dir_status)

    def _load_supplier_registry(self):
        """Load and display supplier_registry.json."""
        self.supplier_table.setRowCount(0)
        registry_path = os.path.join(self.settings.converter_dir(), "supplier_registry.json")

        if not os.path.exists(registry_path):
            return

        try:
            with open(registry_path, "r") as f:
                registry = json.load(f)

            suppliers = registry.get("suppliers", [])
            self.supplier_table.setRowCount(len(suppliers))
            for i, s in enumerate(suppliers):
                self.supplier_table.setItem(i, 0, QTableWidgetItem(s.get("id", "")))
                self.supplier_table.setItem(i, 1, QTableWidgetItem(s.get("name", "")))
                self.supplier_table.setItem(i, 2, QTableWidgetItem(s.get("format", "")))
                self.supplier_table.setItem(i, 3, QTableWidgetItem(s.get("accuracy", "")))
        except Exception as e:
            log.error("[Settings] Failed to load supplier registry: %s", e)

    def _save_settings(self):
        self.settings.set_converter_dir(self.converter_dir_edit.text())
        self.settings.set_template_dir(self.template_dir_edit.text())
        self.settings.set_output_dir(self.output_dir_edit.text())

        self._refresh_all_status()
        log.info("[Settings] Settings saved.")
        self.settings_changed.emit()
