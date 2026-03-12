"""Main application window with tab-based navigation."""

import logging
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QStatusBar, QWidget, QVBoxLayout,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction

from src.config.settings import AppSettings
from src.core.log_handler import QtLogHandler
from src.core.converter import ConversionResult
from src.ui.panels.file_panel import FilePanel
from src.ui.panels.conversion_panel import ConversionPanel
from src.ui.panels.results_panel import ResultsPanel
from src.ui.panels.batch_panel import BatchPanel
from src.ui.panels.settings_panel import SettingsPanel
from src.ui.widgets.trial_banner import TrialBanner, TrialExpiredDialog

log = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self, qt_log_handler: QtLogHandler):
        super().__init__()
        self.settings = AppSettings()
        self.qt_log_handler = qt_log_handler
        self._current_result: ConversionResult | None = None

        self._setup_ui()
        self._connect_signals()
        self._restore_geometry()
        self._check_trial()

    def _setup_ui(self):
        self.setWindowTitle("COA Converter")
        self.setMinimumSize(QSize(900, 650))

        # Central container (banner + tabs)
        central = QWidget()
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)

        self._trial_banner_slot = central_layout  # used by _check_trial

        self.tabs = QTabWidget()
        central_layout.addWidget(self.tabs)
        self.setCentralWidget(central)

        # Tab 1: File Setup
        self.file_panel = FilePanel(self.settings)
        self.tabs.addTab(self.file_panel, "Convert")

        # Tab 2: Conversion Progress
        self.conversion_panel = ConversionPanel(self.qt_log_handler)
        self.tabs.addTab(self.conversion_panel, "Progress")

        # Tab 3: Results
        self.results_panel = ResultsPanel(self.settings)
        self.tabs.addTab(self.results_panel, "Results")

        # Tab 4: Batch Processing
        self.batch_panel = BatchPanel(self.settings)
        self.tabs.addTab(self.batch_panel, "Batch")

        # Tab 5: Settings
        self.settings_panel = SettingsPanel(self.settings)
        self.tabs.addTab(self.settings_panel, "Settings")

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def _connect_signals(self):
        # FilePanel → start conversion
        self.file_panel.start_conversion.connect(self._on_start_conversion)

        # ConversionPanel → pipeline complete
        self.conversion_panel.pipeline_complete.connect(self._on_pipeline_complete)

        # Settings changes
        self.settings_panel.settings_changed.connect(self._on_settings_changed)

    def _on_start_conversion(self, pdf_path: str, template_paths: list, output_dir: str):
        """User clicked 'Start Conversion' in FilePanel."""
        log.info("[MainWindow] Starting conversion: %s → %d template(s)", pdf_path, len(template_paths))
        self.tabs.setCurrentWidget(self.conversion_panel)
        self.conversion_panel.start_multi_pipeline(pdf_path, template_paths, output_dir)
        self.status_bar.showMessage("Converting...")

    def _on_pipeline_complete(self, result):
        """Conversion pipeline finished (single ConversionResult or list)."""
        if isinstance(result, list):
            results = result
            self._current_result = results[-1] if results else None
            success_count = sum(1 for r in results if r.success)
            total = len(results)
            self.status_bar.showMessage(
                f"Conversion complete — {success_count}/{total} succeeded. Check Results tab"
            )
            self.results_panel.show_results(results)
            self.tabs.setCurrentWidget(self.results_panel)
        else:
            self._current_result = result
            if result.success:
                self.status_bar.showMessage("Conversion complete — check Results tab")
                self.results_panel.show_results([result])
                self.tabs.setCurrentWidget(self.results_panel)
            else:
                self.status_bar.showMessage(f"Conversion failed: {result.error}")

    def _on_settings_changed(self):
        """Refresh panels that depend on settings."""
        self.file_panel.refresh_templates()

    def _restore_geometry(self):
        geo = self.settings.window_geometry()
        if geo:
            self.restoreGeometry(geo)
        state = self.settings.window_state()
        if state:
            self.restoreState(state)

    def _check_trial(self):
        """Check trial status and show banner or expiration dialog."""
        remaining = self.settings.trial_remaining_days()
        if self.settings.is_trial_expired():
            log.warning("[MainWindow] Trial expired, blocking access")
            dlg = TrialExpiredDialog(self)
            dlg.exec()
        else:
            log.info("[MainWindow] Trial active, %.1f days remaining", remaining)
            banner = TrialBanner(remaining)
            self._trial_banner_slot.insertWidget(0, banner)

    def closeEvent(self, event):
        self.settings.set_window_geometry(self.saveGeometry())
        self.settings.set_window_state(self.saveState())
        super().closeEvent(event)
