from __future__ import annotations

import datetime
import shutil
import time
from pathlib import Path
from typing import List, Optional

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    HAS_JINJA = True
except ImportError:
    HAS_JINJA = False

from ..c_bridge import bridge
from .aggregators import build_audit_summary
from .models import AuditSummary, LogRecord
from .pure_functions import parse_log_line


class LogAnalyticsEngine:
    def __init__(self, templates_dir: Optional[Path] = None):
        if templates_dir is None:
            self.templates_dir = Path(__file__).resolve().parent.parent.parent.parent / "templates"
        else:
            self.templates_dir = Path(templates_dir)

        if HAS_JINJA:
            self.jinja_env = Environment(
                loader=FileSystemLoader(str(self.templates_dir)),
                autoescape=select_autoescape(["html", "xml"]),
            )
        else:
            self.jinja_env = None

    def analyze_file(self, log_path: Path | str, max_records: Optional[int] = None) -> AuditSummary:
        path = Path(log_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Log file not found: {path}")

        start_time = time.perf_counter()
        engine_label = "C-Accelerated Engine" if bridge.is_available else "Python Pure-Functional Engine"

        records: List[LogRecord] = []
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                rec = parse_log_line(line)
                if rec is not None:
                    records.append(rec)
                    if max_records and len(records) >= max_records:
                        break

        scan_time_ms = (time.perf_counter() - start_time) * 1000.0

        return build_audit_summary(
            records=records,
            engine_name=engine_label,
            scan_time_ms=round(scan_time_ms, 2),
            file_path=str(path.name),
        )

    def generate_html_report(self, summary: AuditSummary, output_path: Path | str) -> Path:
        out_file = Path(output_path).resolve()
        out_file.parent.mkdir(parents=True, exist_ok=True)

        context = {
            "summary": summary,
            "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "year": datetime.date.today().year,
        }

        if self.jinja_env:
            template = self.jinja_env.get_template("audit/dashboard.html")
            html_content = template.render(**context)
        else:
            html_content = self._fallback_render(summary)

        out_file.write_text(html_content, encoding="utf-8")

        assets_src = self.templates_dir / "assets"
        assets_dst = out_file.parent / "assets"
        if assets_src.exists() and not assets_dst.exists():
            shutil.copytree(assets_src, assets_dst)

        return out_file

    def _fallback_render(self, s: AuditSummary) -> str:
        return f"""<!DOCTYPE html>
<html>
<head><title>Audit Report - {s.scanned_file}</title></head>
<body>
<h1>Log Audit Dashboard: {s.scanned_file}</h1>
<p>Total Records: {s.total_records}</p>
<p>Errors: {s.error_count} | Warnings: {s.warning_count} | Critical: {s.critical_count}</p>
<p>Error Rate: {s.error_rate_percent}%</p>
<p>Engine: {s.parsing_engine}</p>
</body>
</html>"""
