from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class LogRecord:
    timestamp: str
    datetime_val: Optional[datetime.datetime]
    level: str
    client_ip: str
    method: str
    endpoint: str
    status_code: int
    response_time_ms: float
    message: str
    raw_line: str

    @property
    def is_error(self) -> bool:
        return self.level in ("ERROR", "CRITICAL", "FATAL") or self.status_code >= 500

    @property
    def is_warning(self) -> bool:
        return self.level in ("WARN", "WARNING") or (400 <= self.status_code < 500)


@dataclass(frozen=True)
class HourlyMetric:
    hour_key: str
    total_requests: int
    error_count: int
    warning_count: int
    avg_latency_ms: float
    error_rate_percent: float


@dataclass(frozen=True)
class AuditSummary:
    total_records: int
    info_count: int
    warning_count: int
    error_count: int
    critical_count: int
    status_2xx: int
    status_3xx: int
    status_4xx: int
    status_5xx: int
    error_rate_percent: float
    peak_hour: str
    peak_hour_requests: int
    avg_latency_ms: float
    p95_latency_ms: float
    top_ips: Tuple[Tuple[str, int], ...]
    top_endpoints: Tuple[Tuple[str, int], ...]
    top_errors: Tuple[Tuple[str, int], ...]
    hourly_series: Tuple[HourlyMetric, ...]
    parsing_engine: str
    execution_time_ms: float
    scanned_file: str
