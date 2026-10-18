"""
Unit Tests for Functional Programming Analytics (Pure Functions, Map, Filter, Reduce).
"""

import unittest
from src.core.analytics.pure_functions import (
    compose,
    pipe,
    parse_log_line,
    is_error,
    is_warning,
    is_level,
    is_status_range,
    extract_client_ip,
)
from src.core.analytics.aggregators import (
    aggregate_frequencies,
    compute_top_k,
    compute_percentile,
    build_audit_summary,
)


class TestFunctionalAnalytics(unittest.TestCase):

    def test_function_composition_and_pipe(self):
        add_two = lambda x: x + 2
        double = lambda x: x * 2

        # pipe(3, add_two, double) == (3 + 2) * 2 == 10
        self.assertEqual(pipe(3, add_two, double), 10)

        # compose(double, add_two)(3) == (3 + 2) * 2 == 10
        self.assertEqual(compose(double, add_two)(3), 10)

    def test_pure_parse_log_line(self):
        raw = "2026-10-18 14:20:00 [ERROR] 192.168.1.50 POST /api/v1/pay 500 120.5ms Connection reset"
        rec = parse_log_line(raw)
        self.assertIsNotNone(rec)
        self.assertEqual(rec.level, "ERROR")
        self.assertEqual(rec.client_ip, "192.168.1.50")
        self.assertEqual(rec.method, "POST")
        self.assertEqual(rec.endpoint, "/api/v1/pay")
        self.assertEqual(rec.status_code, 500)
        self.assertEqual(rec.response_time_ms, 120.5)
        self.assertTrue(rec.is_error)

    def test_pure_predicates(self):
        rec_err = parse_log_line("2026-10-18 14:20:00 [ERROR] 10.0.0.1 GET /err 500 10.0ms Failed")
        rec_warn = parse_log_line("2026-10-18 14:20:00 [WARN] 10.0.0.1 GET /warn 404 10.0ms Not found")
        rec_ok = parse_log_line("2026-10-18 14:20:00 [INFO] 10.0.0.1 GET /ok 200 10.0ms OK")

        self.assertTrue(is_error(rec_err))
        self.assertFalse(is_error(rec_ok))

        self.assertTrue(is_warning(rec_warn))
        self.assertFalse(is_warning(rec_ok))

        is_5xx = is_status_range(500, 599)
        self.assertTrue(is_5xx(rec_err))
        self.assertFalse(is_5xx(rec_ok))

    def test_pure_aggregations_with_map_filter_reduce(self):
        items = ["apple", "banana", "apple", "cherry", "apple", "banana"]
        freq = aggregate_frequencies(items)
        self.assertEqual(freq["apple"], 3)
        self.assertEqual(freq["banana"], 2)
        self.assertEqual(freq["cherry"], 1)

        top = compute_top_k(freq, k=2)
        self.assertEqual(top[0], ("apple", 3))
        self.assertEqual(top[1], ("banana", 2))

    def test_percentile_computation(self):
        values = sorted([10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0])
        p50 = compute_percentile(values, 50.0)
        p95 = compute_percentile(values, 95.0)
        self.assertAlmostEqual(p50, 55.0, delta=1.0)
        self.assertAlmostEqual(p95, 95.5, delta=1.0)


if __name__ == "__main__":
    unittest.main()
