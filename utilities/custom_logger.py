import os
import sys
import time
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# Automatically create required directories
os.makedirs("logs", exist_ok=True)
os.makedirs("screenshots", exist_ok=True)
os.makedirs("output", exist_ok=True)


class FormattedQALogger:
    """
    Enterprise QA Logger Utility producing clean, user-friendly step-by-step business logs.
    CP1252 / Windows console safe formatting with structured tree details and Toast logging.
    """

    def __init__(self, log_file: str = "logs/signature_module.log"):
        self.log_file = log_file
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)

        self.file_logger = logging.getLogger("SignatureAutomationFileLogger")
        self.file_logger.setLevel(logging.DEBUG)

        if not self.file_logger.handlers:
            fh = logging.FileHandler(log_file, mode="a", encoding="utf-8")
            fh.setLevel(logging.DEBUG)
            fh_formatter = logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s")
            fh.setFormatter(fh_formatter)
            self.file_logger.addHandler(fh)

    def _safe_print(self, text: str):
        try:
            print(text)
        except UnicodeEncodeError:
            clean_text = text.encode(sys.stdout.encoding or "ascii", errors="replace").decode(sys.stdout.encoding or "ascii")
            print(clean_text)

    def _format_status(self, status: str) -> str:
        s_upper = status.upper().strip()
        if "PASS" in s_upper:
            return "[PASS] ✓"
        elif "FAIL" in s_upper:
            return "[FAIL] ✗"
        elif "PROGRESS" in s_upper:
            return "[IN_PROGRESS]"
        elif "WARN" in s_upper:
            return "[WARNING]"
        elif "INFO" in s_upper:
            return "[INFO]"
        return f"[{s_upper}]"

    def print_header(self, test_case: str, module: str = "Signature", browser: str = "Chromium", env: str = "STG"):
        header = (
            f"\n{'=' * 75}\n"
            f"TEST CASE : {test_case}\n"
            f"MODULE    : {module}\n"
            f"BROWSER   : {browser}\n"
            f"ENV       : {env}\n"
            f"{'=' * 75}\n"
        )
        self._safe_print(header)
        self.file_logger.info(f"START TEST CASE: {test_case} | MODULE: {module} | ENV: {env}")

    def log_step(
        self,
        step_num: int,
        total_steps: int,
        title: str,
        status: str = "PASS",
        details: Optional[Dict[str, str]] = None,
    ):
        status_formatted = self._format_status(status)
        step_header = f"[{step_num}/{total_steps}] {title:<48} {status_formatted}"
        self._safe_print(step_header)
        self.file_logger.info(f"[{step_num}/{total_steps}] {title:<48} {status}")

        if details:
            for k, v in details.items():
                if isinstance(v, list):
                    v_str = ", ".join(map(str, v))
                else:
                    v_str = str(v)
                detail_line = f"    ├─ {k:<18} : {v_str}"
                self._safe_print(detail_line)
                self.file_logger.info(f"        {k:<18} : {v_str}")
        self._safe_print("")

    def log_toast(self, message: str, field_name: Optional[str] = None):
        """Dedicated logger for UI Toast Notifications captured during form validation."""
        field_info = f" (Field: {field_name})" if field_name else ""
        toast_line = f"    [TOAST CAPTURED]{field_info} -> \"{message}\""
        self._safe_print(toast_line)
        self.file_logger.info(f"TOAST CAPTURED{field_info}: \"{message}\"")

    def print_footer(self, status: str, total_steps: int, passed: int, failed: int, duration_sec: float):
        status_str = "[PASSED] ✓" if "PASS" in status.upper() else "[FAILED] ✗"
        footer = (
            f"\n{'=' * 75}\n"
            f"TEST SUITE EXECUTION SUMMARY\n"
            f"{'-' * 75}\n"
            f"  RESULT     : {status_str}\n"
            f"  TOTAL STEPS: {total_steps}\n"
            f"  PASSED     : {passed}\n"
            f"  FAILED     : {failed}\n"
            f"  DURATION   : {duration_sec:.2f} seconds\n"
            f"{'=' * 75}\n"
        )
        self._safe_print(footer)
        self.file_logger.info(f"TEST STATUS: {status} | DURATION: {duration_sec:.2f}s")



class QALogger(FormattedQALogger):
    pass

