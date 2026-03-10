"""ResultsPanel — Verification results, field comparison, AI analysis."""

import os
import platform
import shutil
import subprocess
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QTextEdit, QTabWidget, QFrame,
    QMessageBox, QComboBox,
)
from PySide6.QtGui import QColor, QFont

from src.config.settings import AppSettings
from src.core.converter import ConversionResult

log = logging.getLogger(__name__)


def _shell_quote(path: str) -> str:
    """Quote a path for shell use, handling spaces and special characters."""
    import shlex
    return shlex.quote(path)


# Colors
COLOR_PASS = QColor("#34C759")
COLOR_FAIL = QColor("#FF3B30")
COLOR_EMPTY = QColor("#888888")


class ResultsPanel(QWidget):
    """Tab 3: Verification results + AI analysis."""

    def __init__(self, settings: AppSettings):
        super().__init__()
        self.settings = settings
        self._result: ConversionResult | None = None
        self._all_results: list[ConversionResult] = []

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Summary bar
        self.summary_frame = QFrame()
        self.summary_frame.setObjectName("summaryFrame")
        summary_layout = QHBoxLayout(self.summary_frame)

        self.status_icon = QLabel("")
        self.status_icon.setStyleSheet("font-size: 24px;")
        summary_layout.addWidget(self.status_icon)

        self.summary_label = QLabel("No results yet. Run a conversion first.")
        self.summary_label.setStyleSheet("font-size: 14px;")
        summary_layout.addWidget(self.summary_label, 1)

        layout.addWidget(self.summary_frame)

        # Result selector (visible only when multiple templates were converted)
        self.result_selector_row = QHBoxLayout()
        self.result_selector_label = QLabel("Template:")
        self.result_selector_label.setStyleSheet("font-weight: bold;")
        self.result_selector_row.addWidget(self.result_selector_label)

        self.result_selector = QComboBox()
        self.result_selector.currentIndexChanged.connect(self._on_result_selected)
        self.result_selector_row.addWidget(self.result_selector, 1)

        self.result_selector_widget = QWidget()
        self.result_selector_widget.setLayout(self.result_selector_row)
        self.result_selector_widget.setVisible(False)
        layout.addWidget(self.result_selector_widget)

        # Sub-tabs for results
        self.sub_tabs = QTabWidget()

        # Sub-tab 1: Field comparison table
        self.comparison_tab = QWidget()
        comp_layout = QVBoxLayout(self.comparison_tab)

        self.comparison_table = QTableWidget()
        self.comparison_table.setColumnCount(4)
        self.comparison_table.setHorizontalHeaderLabels(["Field", "Expected (PDF)", "Actual (Output)", "Status"])
        self.comparison_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.comparison_table.setAlternatingRowColors(True)
        self.comparison_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        comp_layout.addWidget(self.comparison_table)

        self.sub_tabs.addTab(self.comparison_tab, "Field Comparison")

        # Sub-tab 2: Warnings
        self.warnings_tab = QWidget()
        warn_layout = QVBoxLayout(self.warnings_tab)
        self.warnings_text = QTextEdit()
        self.warnings_text.setReadOnly(True)
        warn_layout.addWidget(self.warnings_text)
        self.sub_tabs.addTab(self.warnings_tab, "Warnings")

        # Sub-tab 3: AI Verification
        self.ai_tab = QWidget()
        ai_layout = QVBoxLayout(self.ai_tab)

        ai_btn_row = QHBoxLayout()
        self.ai_verify_btn = QPushButton("Open AI Review (Claude Code)")
        self.ai_verify_btn.setEnabled(False)
        self.ai_verify_btn.clicked.connect(self._run_ai_verification)
        ai_btn_row.addWidget(self.ai_verify_btn)

        self.ai_status_label = QLabel("")
        self.ai_status_label.setStyleSheet("color: #888;")
        ai_btn_row.addWidget(self.ai_status_label, 1)
        ai_layout.addLayout(ai_btn_row)

        self.ai_report_text = QTextEdit()
        self.ai_report_text.setReadOnly(True)
        self.ai_report_text.setFont(QFont("Menlo", 11))
        ai_layout.addWidget(self.ai_report_text)

        self.sub_tabs.addTab(self.ai_tab, "AI Verification")

        layout.addWidget(self.sub_tabs, 1)

        # Action buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.open_file_btn = QPushButton("Open Output File")
        self.open_file_btn.setEnabled(False)
        self.open_file_btn.clicked.connect(self._open_output_file)
        btn_row.addWidget(self.open_file_btn)

        self.open_dir_btn = QPushButton("Open Output Directory")
        self.open_dir_btn.setEnabled(False)
        self.open_dir_btn.clicked.connect(self._open_output_dir)
        btn_row.addWidget(self.open_dir_btn)

        layout.addLayout(btn_row)

    def show_results(self, results: list[ConversionResult]):
        """Populate the panel with one or more conversion results."""
        self._all_results = results

        # Update result selector
        self.result_selector.blockSignals(True)
        self.result_selector.clear()
        for r in results:
            tmpl_name = os.path.basename(r.template_path) if r.template_path else "Unknown"
            status = "OK" if r.success else "FAILED"
            self.result_selector.addItem(f"{tmpl_name} [{status}]")
        self.result_selector.blockSignals(False)

        self.result_selector_widget.setVisible(len(results) > 1)

        # Show first result
        if results:
            self.result_selector.setCurrentIndex(0)
            self._show_single_result(results[0])

    def _on_result_selected(self, index: int):
        """User switched to a different template result."""
        if 0 <= index < len(self._all_results):
            self._show_single_result(self._all_results[index])

    def _show_single_result(self, result: ConversionResult):
        """Populate the panel with a single conversion result."""
        self._result = result

        # Summary
        if result.success:
            self.status_icon.setText("\u2714")
            self.status_icon.setStyleSheet("font-size: 24px; color: #34C759;")
            if result.verification:
                acc = result.verification["accuracy"] * 100
                self.summary_label.setText(
                    f"Conversion successful — {result.verification['passed']}/{result.verification['total']} "
                    f"fields verified ({acc:.0f}% accuracy)"
                )
            else:
                self.summary_label.setText("Conversion successful (no verification for this template type)")
        else:
            self.status_icon.setText("\u2718")
            self.status_icon.setStyleSheet("font-size: 24px; color: #FF3B30;")
            self.summary_label.setText(f"Conversion failed: {result.error}")

        # Field comparison table
        self._populate_comparison_table(result)

        # Warnings
        self.warnings_text.clear()
        if result.warnings:
            for w in result.warnings:
                self.warnings_text.append(f"\u26A0 {w}")
        else:
            self.warnings_text.append("No warnings.")

        # Enable buttons
        self.open_file_btn.setEnabled(result.success and os.path.exists(result.output_path))
        self.open_dir_btn.setEnabled(result.success)
        self.ai_verify_btn.setEnabled(result.success)

        # AI report reset
        self.ai_report_text.clear()
        self.ai_status_label.setText("")

    def _populate_comparison_table(self, result: ConversionResult):
        """Fill the comparison table from verification details."""
        self.comparison_table.setRowCount(0)

        if not result.verification or "details" not in result.verification:
            return

        details = result.verification["details"]
        self.comparison_table.setRowCount(len(details))

        for row, item in enumerate(details):
            # Field name
            self.comparison_table.setItem(row, 0, QTableWidgetItem(item.get("field", "")))

            # Expected
            self.comparison_table.setItem(row, 1, QTableWidgetItem(str(item.get("expected", ""))))

            # Actual
            self.comparison_table.setItem(row, 2, QTableWidgetItem(str(item.get("actual", ""))))

            # Status
            status = item.get("status", "")
            status_item = QTableWidgetItem(status.upper())
            if status == "pass":
                status_item.setForeground(COLOR_PASS)
            elif status == "fail":
                status_item.setForeground(COLOR_FAIL)
            else:
                status_item.setForeground(COLOR_EMPTY)
            self.comparison_table.setItem(row, 3, status_item)

    def _run_ai_verification(self):
        """Open a terminal with Claude Code to perform AI review via coa-to-template skill."""
        if not self._result or not self._result.success:
            return

        # Check claude CLI availability
        claude_bin = shutil.which("claude") or shutil.which("claude.cmd")
        if not claude_bin:
            QMessageBox.warning(
                self,
                "Claude Code Not Found",
                "Could not find 'claude' CLI in PATH.\n\n"
                "Please install Claude Code first:\n"
                "  npm install -g @anthropic-ai/claude-code",
            )
            return

        pdf_path = self._result.pdf_path
        template_path = self._result.template_path
        output_path = self._result.output_path

        # Build the prompt for Claude Code
        prompt = (
            f"/coa-to-template\n"
            f"PDF file: {pdf_path}\n"
            f"Template file: {template_path}\n"
            f"Output file: {output_path}\n"
            f"Please review and fix the output file based on the PDF data and template."
        )

        # Working directory: coa-converter source
        work_dir = self.settings.converter_dir()
        if not os.path.isdir(work_dir):
            work_dir = os.path.dirname(output_path)

        self._open_terminal_with_claude(prompt, work_dir)

        self.ai_status_label.setText("Claude Code launched in terminal")
        self.ai_report_text.clear()
        self.ai_report_text.append(
            "Claude Code has been opened in a new terminal window.\n\n"
            f"Working directory: {work_dir}\n"
            f"PDF: {pdf_path}\n"
            f"Template: {template_path}\n"
            f"Output: {output_path}\n\n"
            "The AI review is running interactively in the terminal.\n"
            "Close the terminal when done."
        )

    def _open_terminal_with_claude(self, prompt: str, work_dir: str):
        """Open a new terminal window and launch claude with the given prompt.

        Writes the prompt to a temp file to avoid shell escaping issues with
        multi-line text, newlines, quotes, and special characters.
        """
        import tempfile

        # Write prompt to a temp file (won't be auto-deleted so the terminal can read it)
        prompt_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", prefix="coa_ai_prompt_", delete=False
        )
        prompt_file.write(prompt)
        prompt_file.close()
        prompt_path = prompt_file.name

        system = platform.system()

        if system == "Darwin":
            shell_cmd = (
                f'cd {_shell_quote(work_dir)} && '
                f'claude --dangerously-skip-permissions "$(cat {_shell_quote(prompt_path)})" ; '
                f'rm -f {_shell_quote(prompt_path)}'
            )
            # Escape for AppleScript string
            shell_cmd_escaped = shell_cmd.replace("\\", "\\\\").replace('"', '\\"')
            apple_script = (
                f'tell application "Terminal"\n'
                f'    do script "{shell_cmd_escaped}"\n'
                f'    activate\n'
                f'end tell'
            )
            subprocess.Popen(["osascript", "-e", apple_script])

        elif system == "Windows":
            # Windows: write a temp .ps1 script to avoid nested quoting issues
            import tempfile as _tf
            script_file = _tf.NamedTemporaryFile(
                mode="w", suffix=".ps1", prefix="coa_ai_launch_", delete=False
            )
            script_path = script_file.name
            script_file.write(
                f'Set-Location -LiteralPath "{work_dir}"\n'
                f'$prompt = Get-Content -Raw -LiteralPath "{prompt_path}"\n'
                f'claude --dangerously-skip-permissions $prompt\n'
                f'Remove-Item -LiteralPath "{prompt_path}" -ErrorAction SilentlyContinue\n'
                f'Remove-Item -LiteralPath "{script_path}" -ErrorAction SilentlyContinue\n'
            )
            script_file.close()
            # Open a new PowerShell window running the script
            subprocess.Popen([
                "powershell", "-Command",
                f'Start-Process powershell -ArgumentList "-NoExit","-File","{script_path}"',
            ])

        else:
            shell_cmd = (
                f"cd {_shell_quote(work_dir)} && "
                f"claude --dangerously-skip-permissions \"$(cat {_shell_quote(prompt_path)})\" ; "
                f"rm -f {_shell_quote(prompt_path)}"
            )
            for term in ["gnome-terminal", "konsole", "xfce4-terminal", "xterm"]:
                if shutil.which(term):
                    if term == "gnome-terminal":
                        subprocess.Popen([term, "--", "bash", "-c", shell_cmd])
                    else:
                        subprocess.Popen([term, "-e", f"bash -c '{shell_cmd}'"])
                    break
            else:
                os.unlink(prompt_path)
                QMessageBox.warning(self, "No Terminal", "Could not find a terminal emulator.")

    def _open_output_file(self):
        if self._result and self._result.output_path:
            _open_path(self._result.output_path)

    def _open_output_dir(self):
        if self._result and self._result.output_path:
            _open_path(os.path.dirname(self._result.output_path))


def _open_path(path: str):
    """Open a file or directory with the OS default handler."""
    system = platform.system()
    if system == "Darwin":
        subprocess.run(["open", path])
    elif system == "Windows":
        os.startfile(path)
    else:
        subprocess.run(["xdg-open", path])
