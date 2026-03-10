"""Wrapper around existing coa_converter module.

Resolves coa-converter modules in dev, frozen (PyInstaller), or co-located
mode, then re-exports the public API for the GUI layer.
"""

import os
import sys
import logging

log = logging.getLogger(__name__)


def _resolve_coa_dir():
    """Locate coa-converter modules in dev, frozen, or co-located mode."""
    # 1. PyInstaller frozen bundle
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
        candidate = os.path.join(base, 'coa_modules')
        if os.path.isdir(candidate):
            return candidate
    # 2. Co-located directory (portable distribution)
    app_dir = os.path.dirname(os.path.abspath(__file__))
    candidate = os.path.normpath(os.path.join(app_dir, '..', '..', 'coa-converter'))
    if os.path.isdir(candidate):
        return candidate
    # 3. Standard dev location
    return os.path.expanduser('~/tools/coa-converter')


_COA_DIR = _resolve_coa_dir()
if _COA_DIR not in sys.path:
    sys.path.insert(0, _COA_DIR)

# Re-export public API from existing modules
from coa_converter import (       # noqa: E402
    convert_coa,
    extract_from_pdf,
    validate_coa,
    fill_template,
    COAData,
)
from template_detector import (    # noqa: E402
    detect_template_layout,
    TemplateLayout,
)
from xlsx_filler import (          # noqa: E402
    fill_xlsx,
    verify_xlsx_output,
)
from supplier_checker import (     # noqa: E402
    check_supplier,
    register_supplier,
    load_registry,
)

# Optional DOCX support
try:
    from docx_filler import fill_docx  # noqa: E402
except ImportError:
    fill_docx = None


class ConversionResult:
    """Structured result from a complete conversion pipeline run."""

    def __init__(self):
        self.pdf_path: str = ""
        self.template_path: str = ""
        self.output_path: str = ""
        self.supplier_info: dict | None = None
        self.coa_data: COAData | None = None
        self.warnings: list[str] = []
        self.layout: TemplateLayout | None = None
        self.verification: dict | None = None
        self.error: str | None = None
        self.success: bool = False


def run_conversion_pipeline(
    pdf_path: str,
    template_path: str,
    output_path: str | None = None,
) -> ConversionResult:
    """Run the full conversion pipeline step by step, returning detailed results.

    Steps:
      1. Check supplier
      2. Extract PDF data
      3. Validate extracted data
      4. Detect template layout
      5. Fill template
      6. Verify output
    """
    result = ConversionResult()
    result.pdf_path = pdf_path
    result.template_path = template_path

    # Default output path
    if output_path is None:
        base = os.path.splitext(os.path.basename(pdf_path))[0]
        ext = os.path.splitext(template_path)[1]
        out_dir = os.path.join(os.path.dirname(template_path), "..", "output")
        out_dir = os.path.abspath(out_dir)
        os.makedirs(out_dir, exist_ok=True)
        output_path = os.path.join(out_dir, f"{base}_filled{ext}")
    result.output_path = output_path

    try:
        # Step 1: Supplier check
        log.info("[Converter] Step 1: Checking supplier...")
        result.supplier_info = check_supplier(pdf_path)
        log.info("[Converter] Supplier: %s", result.supplier_info.get("message", ""))

        # Step 2: Extract
        log.info("[Converter] Step 2: Extracting data from PDF...")
        result.coa_data = extract_from_pdf(pdf_path)
        log.info(
            "[Converter] Extracted: %d analytical, %d microbiology items",
            len(result.coa_data.analytical_items),
            len(result.coa_data.microbiology_items),
        )

        # Step 3: Validate
        log.info("[Converter] Step 3: Validating extracted data...")
        result.warnings = validate_coa(result.coa_data)
        if result.warnings:
            for w in result.warnings:
                log.warning("[Converter] Validation: %s", w)
        else:
            log.info("[Converter] Validation passed — no warnings.")

        # Step 4: Detect layout
        log.info("[Converter] Step 4: Detecting template layout...")
        result.layout = detect_template_layout(template_path)
        log.info(
            "[Converter] Template: %s (%s)",
            result.layout.template_type,
            result.layout.format,
        )

        # Step 5: Fill template
        log.info("[Converter] Step 5: Filling template → %s", output_path)
        fill_template(result.coa_data, template_path, output_path)
        log.info("[Converter] Template filled successfully.")

        # Step 6: Verify output (XLSX COA only)
        if result.layout.format == "xlsx" and result.layout.template_type.startswith("coa_"):
            log.info("[Converter] Step 6: Verifying output...")
            result.verification = verify_xlsx_output(
                result.coa_data, result.layout, output_path, template_path
            )
            log.info(
                "[Converter] Verification: %d/%d passed (%.1f%%)",
                result.verification["passed"],
                result.verification["total"],
                result.verification["accuracy"] * 100,
            )
        else:
            log.info("[Converter] Step 6: Skipped (non-COA XLSX template).")
            result.verification = None

        result.success = True

    except Exception as e:
        log.error("[Converter] Pipeline error: %s", e, exc_info=True)
        result.error = str(e)
        result.success = False

    return result
