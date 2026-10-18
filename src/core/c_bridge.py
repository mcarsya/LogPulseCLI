from __future__ import annotations

import ctypes
import os
import platform
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


class CLogStats(ctypes.Structure):
    _fields_ = [
        ("total_lines", ctypes.c_uint64),
        ("bytes_processed", ctypes.c_uint64),
        ("info_count", ctypes.c_uint32),
        ("warning_count", ctypes.c_uint32),
        ("error_count", ctypes.c_uint32),
        ("critical_count", ctypes.c_uint32),
        ("status_2xx", ctypes.c_uint32),
        ("status_3xx", ctypes.c_uint32),
        ("status_4xx", ctypes.c_uint32),
        ("status_5xx", ctypes.c_uint32),
        ("execution_time_ms", ctypes.c_double),
        ("last_error", ctypes.c_char * 256),
    ]


@dataclass(frozen=True)
class NativeLogStats:
    total_lines: int
    bytes_processed: int
    info_count: int
    warning_count: int
    error_count: int
    critical_count: int
    status_2xx: int
    status_3xx: int
    status_4xx: int
    status_5xx: int
    execution_time_ms: float
    engine: str
    last_error: str = ""

    @property
    def total_errors_and_warnings(self) -> int:
        return self.error_count + self.critical_count + self.warning_count


class CBridge:
    def __init__(self, c_module_dir: Optional[Path] = None):
        if c_module_dir is None:
            c_module_dir = Path(__file__).resolve().parent.parent / "c_modules"
        self.c_module_dir = Path(c_module_dir)
        self.lib: Optional[ctypes.CDLL] = None
        self.load_error: Optional[str] = None
        self._initialize_library()

    def _find_library_path(self) -> Optional[Path]:
        system = platform.system()
        candidates = []
        if system == "Windows":
            candidates = ["logparser.dll", "liblogparser.dll"]
        elif system == "Darwin":
            candidates = ["liblogparser.dylib", "logparser.so"]
        else:
            candidates = ["liblogparser.so", "logparser.so"]

        for name in candidates:
            p = self.c_module_dir / name
            if p.exists():
                return p
        return None

    def _initialize_library(self) -> None:
        lib_path = self._find_library_path()
        if not lib_path:
            self.load_error = f"Binary not found in {self.c_module_dir}"
            return

        try:
            self.lib = ctypes.CDLL(str(lib_path))
            self.lib.parse_log_file.argtypes = [ctypes.c_char_p]
            self.lib.parse_log_file.restype = ctypes.POINTER(CLogStats)
            self.lib.free_log_stats.argtypes = [ctypes.POINTER(CLogStats)]
            self.lib.free_log_stats.restype = None
            self.lib.filter_error_lines.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
            self.lib.filter_error_lines.restype = ctypes.c_int64
            self.lib.get_c_parser_version.argtypes = []
            self.lib.get_c_parser_version.restype = ctypes.c_char_p
        except Exception as exc:
            self.lib = None
            self.load_error = str(exc)

    @property
    def is_available(self) -> bool:
        return self.lib is not None

    def get_version(self) -> str:
        if self.lib and hasattr(self.lib, "get_c_parser_version"):
            return self.lib.get_c_parser_version().decode("utf-8", errors="ignore")
        return "None"

    def parse_file(self, filepath: str | Path) -> NativeLogStats:
        path_str = str(Path(filepath).resolve())
        if not os.path.exists(path_str):
            raise FileNotFoundError(f"File not found: {path_str}")

        if self.is_available and self.lib is not None:
            return self._parse_with_c(path_str)
        return self._parse_with_python_fallback(path_str)

    def _parse_with_c(self, filepath: str) -> NativeLogStats:
        c_path = filepath.encode("utf-8")
        raw_ptr = self.lib.parse_log_file(c_path)  # type: ignore

        if not raw_ptr:
            raise RuntimeError("parse_log_file returned NULL")

        try:
            s = raw_ptr.contents
            return NativeLogStats(
                total_lines=int(s.total_lines),
                bytes_processed=int(s.bytes_processed),
                info_count=int(s.info_count),
                warning_count=int(s.warning_count),
                error_count=int(s.error_count),
                critical_count=int(s.critical_count),
                status_2xx=int(s.status_2xx),
                status_3xx=int(s.status_3xx),
                status_4xx=int(s.status_4xx),
                status_5xx=int(s.status_5xx),
                execution_time_ms=float(s.execution_time_ms),
                engine=f"C-Native ({self.get_version()})",
                last_error=s.last_error.decode("utf-8", errors="ignore").strip(),
            )
        finally:
            self.lib.free_log_stats(raw_ptr)  # type: ignore

    def _parse_with_python_fallback(self, filepath: str) -> NativeLogStats:
        start_time = time.perf_counter()
        total_lines = 0
        bytes_processed = 0
        info_count = 0
        warning_count = 0
        error_count = 0
        critical_count = 0
        status_2xx = 0
        status_3xx = 0
        status_4xx = 0
        status_5xx = 0

        with open(filepath, "rb") as f:
            for raw_line in f:
                bytes_processed += len(raw_line)
                total_lines += 1
                line = raw_line.decode("utf-8", errors="ignore").upper()

                if "CRITICAL" in line or "FATAL" in line or "[CRIT]" in line:
                    critical_count += 1
                elif "ERROR" in line or "[ERR]" in line or "EXCEPTION" in line:
                    error_count += 1
                elif "WARN" in line or "WARNING" in line or "[WARN]" in line:
                    warning_count += 1
                elif "INFO" in line or "[INFO]" in line:
                    info_count += 1

                if " 200 " in line or " 201 " in line or " 204 " in line:
                    status_2xx += 1
                elif " 301 " in line or " 302 " in line or " 304 " in line:
                    status_3xx += 1
                elif " 400 " in line or " 401 " in line or " 403 " in line or " 404 " in line or " 429 " in line:
                    status_4xx += 1
                elif " 500 " in line or " 502 " in line or " 503 " in line or " 504 " in line:
                    status_5xx += 1

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return NativeLogStats(
            total_lines=total_lines,
            bytes_processed=bytes_processed,
            info_count=info_count,
            warning_count=warning_count,
            error_count=error_count,
            critical_count=critical_count,
            status_2xx=status_2xx,
            status_3xx=status_3xx,
            status_4xx=status_4xx,
            status_5xx=status_5xx,
            execution_time_ms=elapsed_ms,
            engine="Python-Fallback (Streaming)",
            last_error="",
        )


bridge = CBridge()
