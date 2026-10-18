from __future__ import annotations

import functools
from collections import defaultdict
from typing import Callable, Dict, Iterable, List, Sequence, Tuple, TypeVar

from .models import AuditSummary, HourlyMetric, LogRecord
from .pure_functions import (
    extract_client_ip,
    extract_endpoint,
    extract_hour_key,
    extract_response_time,
    is_error,
    is_level,
    is_status_range,
    is_warning,
)

T = TypeVar("T")


def frequency_reducer(accumulator: Dict[T, int], item: T) -> Dict[T, int]:
    accumulator[item] = accumulator.get(item, 0) + 1
    return accumulator


def sum_reducer(acc: float, val: float) -> float:
    return acc + val


def aggregate_frequencies(items: Iterable[T]) -> Dict[T, int]:
    return functools.reduce(frequency_reducer, items, {})


def compute_top_k(frequency_map: Dict[T, int], k: int = 5) -> Tuple[Tuple[T, int], ...]:
    sorted_pairs = sorted(frequency_map.items(), key=lambda pair: pair[1], reverse=True)
    return tuple(sorted_pairs[:k])


def compute_percentile(sorted_values: Sequence[float], percentile: float) -> float:
    if not sorted_values:
        return 0.0
    k = (len(sorted_values) - 1) * (percentile / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_values) - 1)
    d0 = sorted_values[f] * (c - k)
    d1 = sorted_values[c] * (k - f)
    return round(d0 + d1, 2)


def aggregate_hourly_time_series(records: Sequence[LogRecord]) -> Tuple[HourlyMetric, ...]:
    if not records:
        return ()

    hourly_buckets: Dict[str, List[LogRecord]] = defaultdict(list)
    for record in records:
        hourly_buckets[extract_hour_key(record)].append(record)

    metrics_list: List[HourlyMetric] = []
    for hour_key in sorted(hourly_buckets.keys()):
        hour_records = hourly_buckets[hour_key]
        total = len(hour_records)

        err_count = len(list(filter(is_error, hour_records)))
        warn_count = len(list(filter(is_warning, hour_records)))

        latencies = list(map(extract_response_time, hour_records))
        total_latency = functools.reduce(sum_reducer, latencies, 0.0)
        avg_lat = round(total_latency / total, 2) if total > 0 else 0.0
        err_rate = round((err_count / total) * 100.0, 2) if total > 0 else 0.0

        metrics_list.append(
            HourlyMetric(
                hour_key=hour_key,
                total_requests=total,
                error_count=err_count,
                warning_count=warn_count,
                avg_latency_ms=avg_lat,
                error_rate_percent=err_rate,
            )
        )

    return tuple(metrics_list)


def build_audit_summary(
    records: Sequence[LogRecord],
    engine_name: str,
    scan_time_ms: float,
    file_path: str,
) -> AuditSummary:
    total = len(records)
    if total == 0:
        return AuditSummary(
            total_records=0,
            info_count=0,
            warning_count=0,
            error_count=0,
            critical_count=0,
            status_2xx=0,
            status_3xx=0,
            status_4xx=0,
            status_5xx=0,
            error_rate_percent=0.0,
            peak_hour="N/A",
            peak_hour_requests=0,
            avg_latency_ms=0.0,
            p95_latency_ms=0.0,
            top_ips=(),
            top_endpoints=(),
            top_errors=(),
            hourly_series=(),
            parsing_engine=engine_name,
            execution_time_ms=scan_time_ms,
            scanned_file=file_path,
        )

    info_count = len(list(filter(is_level("INFO"), records)))
    warn_count = len(list(filter(is_warning, records)))
    error_count = len(list(filter(is_level("ERROR"), records)))
    crit_count = len(list(filter(is_level("CRITICAL"), records)))

    status_2xx = len(list(filter(is_status_range(200, 299), records)))
    status_3xx = len(list(filter(is_status_range(300, 399), records)))
    status_4xx = len(list(filter(is_status_range(400, 499), records)))
    status_5xx = len(list(filter(is_status_range(500, 599), records)))

    total_failures = error_count + crit_count + status_5xx
    error_rate = round((total_failures / total) * 100.0, 2)

    ip_frequencies = aggregate_frequencies(map(extract_client_ip, records))
    top_ips = compute_top_k(ip_frequencies, k=5)

    endpoint_frequencies = aggregate_frequencies(map(extract_endpoint, records))
    top_endpoints = compute_top_k(endpoint_frequencies, k=5)

    error_records = filter(is_error, records)
    error_messages = map(
        lambda r: f"[{r.status_code}] {r.endpoint} - {r.message}" if r.message else f"[{r.status_code}] {r.endpoint}",
        error_records
    )
    error_freq = aggregate_frequencies(error_messages)
    top_errors = compute_top_k(error_freq, k=5)

    latencies = sorted(list(map(extract_response_time, records)))
    sum_latency = functools.reduce(sum_reducer, latencies, 0.0)
    avg_latency = round(sum_latency / total, 2)
    p95_latency = compute_percentile(latencies, 95.0)

    hourly_series = aggregate_hourly_time_series(records)

    if hourly_series:
        peak_metric = max(hourly_series, key=lambda m: m.total_requests)
        peak_hour = peak_metric.hour_key
        peak_hour_requests = peak_metric.total_requests
    else:
        peak_hour = "N/A"
        peak_hour_requests = 0

    return AuditSummary(
        total_records=total,
        info_count=info_count,
        warning_count=warn_count,
        error_count=error_count,
        critical_count=crit_count,
        status_2xx=status_2xx,
        status_3xx=status_3xx,
        status_4xx=status_4xx,
        status_5xx=status_5xx,
        error_rate_percent=error_rate,
        peak_hour=peak_hour,
        peak_hour_requests=peak_hour_requests,
        avg_latency_ms=avg_latency,
        p95_latency_ms=p95_latency,
        top_ips=top_ips,
        top_endpoints=top_endpoints,
        top_errors=top_errors,
        hourly_series=hourly_series,
        parsing_engine=engine_name,
        execution_time_ms=scan_time_ms,
        scanned_file=file_path,
    )
