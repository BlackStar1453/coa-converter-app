"""QThread workers for background conversion and AI verification."""

import os
import logging
from PySide6.QtCore import QThread, Signal

from src.core.converter import (
    ConversionResult,
    check_supplier,
    extract_from_pdf,
    validate_coa,
    detect_template_layout,
    fill_template,
    verify_xlsx_output,
)

log = logging.getLogger(__name__)


class ConversionWorker(QThread):
    """Runs the conversion pipeline in a background thread.

    Emits step-by-step progress signals so the UI can update a pipeline view.

    Signals:
        step_started(int, str)      - (step_index, step_description)
        step_finished(int, dict)    - (step_index, step_result_data)
        pipeline_finished(ConversionResult)
        error_occurred(str)
    """

    step_started = Signal(int, str)
    step_finished = Signal(int, object)
    pipeline_finished = Signal(object)  # ConversionResult
    error_occurred = Signal(str)

    STEPS = [
        "Checking supplier",
        "Extracting PDF data",
        "Validating data",
        "Detecting template layout",
        "Filling template",
        "Verifying output",
    ]

    def __init__(self, pdf_path: str, template_path: str, output_path: str):
        super().__init__()
        self.pdf_path = pdf_path
        self.template_path = template_path
        self.output_path = output_path
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        result = ConversionResult()
        result.pdf_path = self.pdf_path
        result.template_path = self.template_path
        result.output_path = self.output_path

        try:
            # Step 0: Supplier check
            self.step_started.emit(0, self.STEPS[0])
            result.supplier_info = check_supplier(self.pdf_path)
            self.step_finished.emit(0, result.supplier_info)
            if self._cancelled:
                return

            # Step 1: Extract
            self.step_started.emit(1, self.STEPS[1])
            result.coa_data = extract_from_pdf(self.pdf_path)
            self.step_finished.emit(1, {
                "analytical": len(result.coa_data.analytical_items),
                "microbiology": len(result.coa_data.microbiology_items),
                "header_fields": len(result.coa_data.header),
            })
            if self._cancelled:
                return

            # Step 2: Validate
            self.step_started.emit(2, self.STEPS[2])
            result.warnings = validate_coa(result.coa_data)
            self.step_finished.emit(2, {"warnings": result.warnings})
            if self._cancelled:
                return

            # Step 3: Detect layout
            self.step_started.emit(3, self.STEPS[3])
            result.layout = detect_template_layout(self.template_path)
            self.step_finished.emit(3, {
                "type": result.layout.template_type,
                "format": result.layout.format,
            })
            if self._cancelled:
                return

            # Step 4: Fill template
            self.step_started.emit(4, self.STEPS[4])
            fill_template(result.coa_data, self.template_path, self.output_path)
            self.step_finished.emit(4, {"output": self.output_path})
            if self._cancelled:
                return

            # Step 5: Verify
            self.step_started.emit(5, self.STEPS[5])
            if result.layout.format == "xlsx" and result.layout.template_type.startswith("coa_"):
                result.verification = verify_xlsx_output(
                    result.coa_data, result.layout, self.output_path, self.template_path
                )
                self.step_finished.emit(5, result.verification)
            else:
                self.step_finished.emit(5, {"skipped": True})

            result.success = True

        except Exception as e:
            log.error("[Worker] Error: %s", e, exc_info=True)
            result.error = str(e)
            result.success = False
            self.error_occurred.emit(str(e))

        self.pipeline_finished.emit(result)


class AIVerificationWorker(QThread):
    """Runs Claude Agent SDK verification in a background thread.

    Signals:
        progress(str)           - status text updates
        finished(dict)          - verification result dict
        error_occurred(str)     - error message
    """

    progress = Signal(str)
    finished = Signal(object)
    error_occurred = Signal(str)

    def __init__(self, api_key: str, pdf_path: str, template_path: str, output_path: str, model: str = "claude-sonnet-4-20250514"):
        super().__init__()
        self.api_key = api_key
        self.pdf_path = pdf_path
        self.template_path = template_path
        self.output_path = output_path
        self.model = model
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            self.progress.emit("Initializing AI verification agent...")
            from src.core.ai_verifier import COAVerificationAgent

            agent = COAVerificationAgent(self.api_key, model=self.model)

            self.progress.emit("Agent analyzing PDF, template, and output files...")
            result = agent.verify(self.pdf_path, self.template_path, self.output_path)

            if self._cancelled:
                return

            self.progress.emit("AI verification complete.")
            self.finished.emit(result)

        except Exception as e:
            log.error("[AIWorker] Error: %s", e, exc_info=True)
            self.error_occurred.emit(str(e))


class BatchConversionWorker(QThread):
    """Processes multiple PDF files sequentially.

    Signals:
        file_started(int, str)              - (index, pdf_filename)
        file_finished(int, ConversionResult) - (index, result)
        batch_finished(list)                 - list[ConversionResult]
        error_occurred(int, str)             - (index, error_message)
    """

    file_started = Signal(int, str)
    file_finished = Signal(int, object)
    batch_finished = Signal(list)
    error_occurred = Signal(int, str)

    def __init__(self, file_list: list[tuple[str, str, str]]):
        """file_list: list of (pdf_path, template_path, output_path)"""
        super().__init__()
        self.file_list = file_list
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        from src.core.converter import run_conversion_pipeline

        results = []
        for i, (pdf_path, template_path, output_path) in enumerate(self.file_list):
            if self._cancelled:
                break

            self.file_started.emit(i, os.path.basename(pdf_path))

            try:
                r = run_conversion_pipeline(pdf_path, template_path, output_path)
                results.append(r)
                self.file_finished.emit(i, r)
            except Exception as e:
                self.error_occurred.emit(i, str(e))
                r = ConversionResult()
                r.error = str(e)
                results.append(r)

        self.batch_finished.emit(results)
