"""Persistent application settings using QSettings."""

import os
import platform
import hashlib
import time
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

TRIAL_DAYS = 3
_TRIAL_SALT = "coa_conv_2024_salt"


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

    # --- Trial period ---
    @staticmethod
    def _trial_signature(timestamp: str) -> str:
        """Generate a simple HMAC-like signature for tamper detection."""
        raw = f"{_TRIAL_SALT}:{timestamp}".encode()
        return hashlib.sha256(raw).hexdigest()[:16]

    def trial_first_launch(self) -> float | None:
        """Return the first-launch epoch timestamp, or None if not set."""
        ts = self._s.value("internal/t_start")
        sig = self._s.value("internal/t_sig")
        if ts is None or sig is None:
            return None
        ts_str = str(ts)
        if self._trial_signature(ts_str) != str(sig):
            return None  # tampered — treat as expired
        try:
            return float(ts_str)
        except (ValueError, TypeError):
            return None

    def ensure_trial_start(self) -> float:
        """Record the first-launch time if not already set; return it."""
        existing = self.trial_first_launch()
        if existing is not None:
            return existing
        now = time.time()
        ts_str = str(now)
        self._s.setValue("internal/t_start", ts_str)
        self._s.setValue("internal/t_sig", self._trial_signature(ts_str))
        return now

    def trial_remaining_days(self) -> float:
        """Return remaining trial days (can be negative if expired)."""
        start = self.ensure_trial_start()
        elapsed = time.time() - start
        return TRIAL_DAYS - (elapsed / 86400)

    def is_trial_expired(self) -> bool:
        return self.trial_remaining_days() <= 0
