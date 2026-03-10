"""Persistent application settings using QSettings."""

import os
import platform
from PySide6.QtCore import QSettings


def _default_converter_dir() -> str:
    """Return platform-appropriate default path for coa-converter."""
    home = os.path.expanduser("~")
    if platform.system() == "Windows":
        return os.path.join(home, "tools", "coa-converter")
    return os.path.join(home, "tools", "coa-converter")


COA_CONVERTER_DIR = _default_converter_dir()
DEFAULT_TEMPLATE_DIR = os.path.join(COA_CONVERTER_DIR, "templates")
DEFAULT_OUTPUT_DIR = os.path.join(COA_CONVERTER_DIR, "output")

ORGANIZATION = "COAConverter"
APPLICATION = "COA Converter"


class AppSettings:
    """Wrapper around QSettings for typed access."""

    def __init__(self):
        self._s = QSettings(ORGANIZATION, APPLICATION)

    # --- Template directory ---
    def template_dir(self) -> str:
        return self._s.value("paths/template_dir", DEFAULT_TEMPLATE_DIR, str)

    def set_template_dir(self, path: str):
        self._s.setValue("paths/template_dir", path)

    # --- Output directory ---
    def output_dir(self) -> str:
        return self._s.value("paths/output_dir", DEFAULT_OUTPUT_DIR, str)

    def set_output_dir(self, path: str):
        self._s.setValue("paths/output_dir", path)

    # --- COA Converter source directory ---
    def converter_dir(self) -> str:
        return self._s.value("paths/converter_dir", COA_CONVERTER_DIR, str)

    def set_converter_dir(self, path: str):
        self._s.setValue("paths/converter_dir", path)

    # --- Window geometry ---
    def window_geometry(self):
        return self._s.value("ui/geometry")

    def set_window_geometry(self, geometry):
        self._s.setValue("ui/geometry", geometry)

    def window_state(self):
        return self._s.value("ui/state")

    def set_window_state(self, state):
        self._s.setValue("ui/state", state)
