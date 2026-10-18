"""
Unit Tests for C Bridge & Fallback Architecture.
"""

import unittest
from pathlib import Path
from src.core.c_bridge import CBridge, NativeLogStats, bridge


class TestCBridge(unittest.TestCase):

    def test_singleton_bridge_instance(self):
        self.assertIsNotNone(bridge)
        # Even if not compiled, is_available is a boolean
        self.assertIsInstance(bridge.is_available, bool)

    def test_python_fallback_execution(self):
        log_file = Path("sample_logs/server_production.log")
        if log_file.exists():
            stats = bridge.parse_file(log_file)
            self.assertIsInstance(stats, NativeLogStats)
            self.assertGreater(stats.total_lines, 0)
            self.assertGreater(stats.bytes_processed, 0)
            self.assertGreaterEqual(stats.error_count, 0)
            self.assertGreaterEqual(stats.warning_count, 0)
            self.assertIn("Fallback", stats.engine) if not bridge.is_available else self.assertIn("C-Native", stats.engine)


if __name__ == "__main__":
    unittest.main()
