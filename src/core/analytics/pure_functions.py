"""
LogPulse CLI - Pure Functions & Combinators (Functional Programming)
Implements side-effect-free pure functions, composition combinators, and currying.
"""

from __future__ import annotations

import datetime
import functools
import re
from typing import Any, Callable, Optional, Sequence, TypeVar

from .models import LogRecord

T = TypeVar("T")
U = TypeVar("U")
V = TypeVar("V")


# ================= Combinators & Higher-Order Functions =================

def compose(*functions: Callable[[Any], Any]) -> Callable[[Any], Any]:
    """
    Mathematical function composition: compose(f, g)(x) == f(g(x)).
    Evaluates functions right-to-left.
    """
    def _composed(initial_val: Any) -> Any:
        return functools.reduce(lambda acc, f: f(acc), reversed(functions), initial_val)
    return _composed


def pipe(initial_val: T, *functions: Callable[[Any], Any]) -> Any:
    """
    Pipeline evaluation: pipe(x, f, g) == g(f(x)).
    Evaluates functions left-to-right.
    """
    return functools.reduce(lambda acc, f: f(acc), functions, initial_val)


def curry_2(fn: Callable[[T, U], V]) -> Callable[[T], Callable[[U], V]]:
    """Curries a 2-argument pure function into two 1-argument functions."""
    def curried_first(a: T) -> Callable[[U], V]:
        def curried_second(b: U) -> V:
            return fn(a, b)
        return curried_second
    return curried_first


# ================= Pure Parsing Functions =================

# RegEx for enterprise log format:
# Example: 2026-10-18 14:22:01 [ERROR] 192.168.1.45 POST /api/v1/payments 500 245.2ms Database timeout
ENTERPRISE_PATTERN = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)\s+"
    r"\[(?P<level>[A-Z]+)\]\s+"
    r"(?P<ip>\d{1,3}(?:\.\d{1,3}){3}|[a-fA-F0-9:]+)\s+"
    r"(?P<method>[A-Z]+)\s+"
    r"(?P<endpoint>\S+)\s+"
    r"(?P<status>\d{3})\s+"
    r"(?P<latency>\d+(?:\.\d+)?)(?:ms)?\s*"
    r"(?P<message>.*)$"
)

# Common/Combined Log Format fallback:
# Example: 192.168.1.1 - - [18/Oct/2026:14:22:01 +0000] "GET /api/v1/users HTTP/1.1" 200 1234
CLF_PATTERN = re.compile(
    r"^(?P<ip>\S+)\s+\S+\s+\S+\s+\[(?P<timestamp>[^\]]+)\]\s+\"(?P<method>[A-Z]+)\s+(?P<endpoint>\S+)\s+[^\"]+\"\s+(?P<status>\d{3})\s+(?P<bytes>\S+)(?:\s+(?P<latency>\d+(?:\.\d+)?))?"
)


def parse_timestamp_iso(ts_str: str) -> Optional[datetime.datetime]:
    """Pure parsing of datetime strings without exceptions leaking."""
    clean = ts_str.replace("T", " ").split(".")[0].split("+")[0].split("Z")[0].strip()
    try:
        return datetime.datetime.strptime(clean, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        try:
            return datetime.datetime.strptime(clean, "%d/%b/%Y:%H:%M:%S")
        except ValueError:
            return None


def parse_log_line(raw_line: str) -> Optional[LogRecord]:
    """
    Pure function: Given an immutable string, returns an immutable LogRecord or None.
    Zero side-effects.
    """
    line = raw_line.strip()
    if not line:
        return None

    # Try Enterprise format first
    m = ENTERPRISE_PATTERN.match(line)
    if m:
        ts_str = m.group("timestamp")
        status = int(m.group("status"))
        latency = float(m.group("latency"))
        return LogRecord(
            timestamp=ts_str,
            datetime_val=parse_timestamp_iso(ts_str),
            level=m.group("level").upper(),
            client_ip=m.group("ip"),
            method=m.group("method").upper(),
            endpoint=m.group("endpoint"),
            status_code=status,
            response_time_ms=latency,
            message=m.group("message").strip(),
            raw_line=raw_line,
        )

    # Try CLF format
    m_clf = CLF_PATTERN.match(line)
    if m_clf:
        ts_str = m_clf.group("timestamp")
        status = int(m_clf.group("status"))
        raw_lat = m_clf.group("latency")
        latency = float(raw_lat) if raw_lat else 0.0
        level = "ERROR" if status >= 500 else ("WARN" if status >= 400 else "INFO")
        return LogRecord(
            timestamp=ts_str,
            datetime_val=parse_timestamp_iso(ts_str),
            level=level,
            client_ip=m_clf.group("ip"),
            method=m_clf.group("method").upper(),
            endpoint=m_clf.group("endpoint"),
            status_code=status,
            response_time_ms=latency,
            message="",
            raw_line=raw_line,
        )

    # Fallback heuristic parser for arbitrary server logs
    upper_line = line.upper()
    level = "INFO"
    if "CRITICAL" in upper_line or "FATAL" in upper_line:
        level = "CRITICAL"
    elif "ERROR" in upper_line or "EXCEPTION" in upper_line:
        level = "ERROR"
    elif "WARN" in upper_line:
        level = "WARN"

    # Search for status code
    status_match = re.search(r"\b([2-5]\d{2})\b", line)
    status_code = int(status_match.group(1)) if status_match else 200

    # Search for IP
    ip_match = re.search(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", line)
    client_ip = ip_match.group(0) if ip_match else "127.0.0.1"

    # Search for endpoint
    endpoint_match = re.search(r"(/[\w\-./]*)", line)
    endpoint = endpoint_match.group(1) if endpoint_match else "/"

    return LogRecord(
        timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        datetime_val=None,
        level=level,
        client_ip=client_ip,
        method="GET",
        endpoint=endpoint,
        status_code=status_code,
        response_time_ms=0.0,
        message=line,
        raw_line=raw_line,
    )


# ================= Pure Predicates =================

def is_error(record: LogRecord) -> bool:
    """Predicate: returns True if record indicates error or critical failure."""
    return record.is_error


def is_warning(record: LogRecord) -> bool:
    """Predicate: returns True if record indicates a warning or client error."""
    return record.is_warning


def is_level(target_level: str) -> Callable[[LogRecord], bool]:
    """Curried predicate: filters records by specific level."""
    target = target_level.upper()
    def _predicate(record: LogRecord) -> bool:
        return record.level == target
    return _predicate


def is_status_range(min_code: int, max_code: int) -> Callable[[LogRecord], bool]:
    """Curried predicate: filters records by status code interval [min_code, max_code]."""
    def _predicate(record: LogRecord) -> bool:
        return min_code <= record.status_code <= max_code
    return _predicate


# ================= Pure Extractors =================

def extract_client_ip(record: LogRecord) -> str:
    """Pure extractor: Client IP."""
    return record.client_ip


def extract_endpoint(record: LogRecord) -> str:
    """Pure extractor: HTTP Endpoint path."""
    return record.endpoint


def extract_status_code(record: LogRecord) -> int:
    """Pure extractor: HTTP status code."""
    return record.status_code


def extract_response_time(record: LogRecord) -> float:
    """Pure extractor: Response latency in ms."""
    return record.response_time_ms


def extract_hour_key(record: LogRecord) -> str:
    """Pure extractor: Formats hour key (YYYY-MM-DD HH:00)."""
    if record.datetime_val:
        return record.datetime_val.strftime("%Y-%m-%d %H:00")
    if len(record.timestamp) >= 13 and "-" in record.timestamp:
        return record.timestamp[:13] + ":00"
    return "Unknown Hour"
