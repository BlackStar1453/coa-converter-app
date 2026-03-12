# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

COA (Certificate of Analysis) PDF-to-Template Converter — a Python desktop application using PySide6 (Qt) that converts supplier COA PDFs into structured Excel/Word templates. Supports batch processing and Claude AI-powered verification. Distributed as standalone executables for macOS and Windows via PyInstaller.

## Development Commands

```bash
# Run the app (development)
./run.sh                              # macOS/Linux
.venv/bin/python -m src.main          # Alternative

# Build standalone executable
pyinstaller --noconfirm "COA Converter.spec"              # macOS → dist/COA Converter.app
pyinstaller --noconfirm "COA Converter Windows.spec"      # Windows → dist/COA Converter/

# Install dependencies
pip install -r requirements.txt
```

No test framework is currently configured. No lint or format commands are set up.

## Architecture

### Tech Stack
- **Python 3.12+**, **PySide6-Essentials** (GUI), **PyInstaller** (packaging)
- **pdfplumber / PyMuPDF** (PDF extraction), **openpyxl** (Excel), **python-docx** (Word)
- **anthropic SDK** (AI verification via Claude Agent)

### Source Structure (`src/`)

- **`main.py`** — Entry point, logging setup, launches `MainWindow`
- **`config/settings.py`** — QSettings wrapper: trial period (3-day with HMAC tamper detection), directory paths, window state
- **`core/`** — Business logic
  - `converter.py` — Wraps external `coa-converter` module; `run_conversion_pipeline()` executes 6-step process (check supplier → extract PDF → validate → detect layout → fill template → verify)
  - `workers.py` — QThread workers (`ConversionWorker`, `BatchConversionWorker`) for background processing
  - `template_manager.py` — Template discovery and metadata (`scan_templates()`, `TemplateInfo`)
  - `ai_verifier.py` — Claude Agent SDK verification with custom MCP tools for PDF/XLSX reading
  - `log_handler.py` — Bridges Python logging → Qt signals for real-time UI log display
- **`ui/`** — GUI layer
  - `main_window.py` — QMainWindow with 5 tabs + trial expiration banner
  - `panels/` — Tab panels: `file_panel` (PDF/template selection with drag-drop), `conversion_panel` (6-step progress + live logs), `results_panel` (verification results + export), `batch_panel` (multi-file queue processing), `settings_panel` (config + supplier registry)
  - `widgets/trial_banner.py` — Trial period UI (banner + blocking dialog)
- **`styles/theme.qss`** — macOS-inspired Qt stylesheet

### Key Patterns

**Signal-Slot (Qt):** UI panels communicate via Qt signals. Workers run on QThread and emit progress/completion signals back to the UI thread.

**External module dependency:** The core conversion logic lives in a separate `coa-converter` repo (`BlackStar1453/coa-converter`). Path resolution in `converter.py` checks: frozen (PyInstaller) bundle → co-located directory → `~/tools/coa-converter` fallback.

**6-step conversion pipeline:** Each step emits progress signals rendered as step indicators in the UI (⬘ pending → ▶ running → ✔ done / ✘ failed).

### Build & Distribution

- **PyInstaller specs** handle hidden imports, data file bundling (theme.qss, coa_modules), and cross-platform icon support
- **CI/CD** (`.github/workflows/build-release.yml`): triggered by `v*` tags or manual dispatch; builds on both macOS and Windows runners, creates GitHub Release with zipped artifacts
- Both specs include multi-path resolution for the external `coa-converter` module (CI checkout layouts, local dev, portable distribution)
