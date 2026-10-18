from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Optional

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich import print as rprint
    HAS_RICH = True
    console = Console(force_terminal=True, legacy_windows=False)
except Exception:
    HAS_RICH = False
    console = None

from .c_bridge import bridge
from .ssg.generator import StaticSiteGenerator
from .analytics.engine import LogAnalyticsEngine


def print_banner() -> None:
    banner = r"""
  _                   ____        _            ____ _     ___ 
 | |    ___   __ _  |  _ \ _   _| |___  ___  / ___| |   |_ _|
 | |   / _ \ / _` | | |_) | | | | / __|/ _ \| |   | |    | | 
 | |__| (_) | (_| | |  __/| |_| | \__ \  __/| |___| |___ | | 
 |_____\___/ \__, | |_|    \__,_|_|___/\___| \____|_____|___|
             |___/   Enterprise Documentation & Log Audit CLI
    """
    if console:
        console.print(f"[bold cyan]{banner}[/bold cyan]")
    else:
        print(banner)


def cmd_status(args: argparse.Namespace) -> int:
    print_banner()
    c_status = "[bold green]LINKED (Active)[/bold green]" if bridge.is_available else "[bold yellow]NOT COMPILED (Fallback Active)[/bold yellow]"
    c_version = bridge.get_version()

    if console:
        table = Table(title="LogPulse CLI System Diagnostic", show_header=True, header_style="bold magenta")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Details", style="dim")

        table.add_row("Python Runtime", f"v{sys.version.split()[0]}", sys.executable)
        table.add_row("C Acceleration Engine", c_status, f"Version: {c_version}")
        table.add_row("C Shared Lib Directory", str(bridge.c_module_dir), "logparser.so / logparser.dll")
        table.add_row("SSG Architecture", "[bold green]Ready[/bold green]", "OOP + N-ary Tree DS + Jinja2")
        table.add_row("Analytics Engine", "[bold green]Ready[/bold green]", "Functional Programming (map, filter, reduce)")

        console.print(table)
        if not bridge.is_available and bridge.load_error:
            console.print(f"\n[dim yellow]Note on C Module: {bridge.load_error}[/dim yellow]")
            console.print("[dim green]To compile C engine: run 'make' or 'bash scripts/build.sh'[/dim green]\n")
    else:
        print("=== LogPulse CLI System Diagnostic ===")
        print(f"Python Runtime: v{sys.version.split()[0]}")
        print(f"C Acceleration Engine: {'LINKED' if bridge.is_available else 'FALLBACK'}")
        print(f"C Shared Lib Path: {bridge.c_module_dir}")

    return 0


def cmd_build_docs(args: argparse.Namespace) -> int:
    docs_dir = Path(args.docs_dir)
    output_dir = Path(args.output_dir)

    if console:
        console.print(f"[bold blue]>>> Starting Static Site Generator (SSG)...[/bold blue]")
        console.print(f"  Docs Source: [cyan]{docs_dir}[/cyan]")
        console.print(f"  Output Dir : [cyan]{output_dir}[/cyan]\n")
    else:
        print(f">>> Building docs from {docs_dir} to {output_dir}...")

    try:
        ssg = StaticSiteGenerator(docs_dir=docs_dir, output_dir=output_dir)
        result = ssg.build()

        if console:
            table = Table(title="Documentation Build Summary", show_header=True, header_style="bold green")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="bold white")

            table.add_row("Total SOP Documents", str(result.total_documents))
            table.add_row("Hierarchy Categories", str(result.total_categories))
            table.add_row("Target Directory", str(result.output_directory))
            table.add_row("Build Elapsed Time", f"{result.elapsed_seconds:.3f} s")
            table.add_row("Entrypoint Page", str(result.output_directory / "index.html"))

            console.print(table)
            console.print(f"\n[bold green][SUCCESS] Documentation portal generated successfully![/bold green]")
            console.print(f"Open in browser: [underline cyan]{(result.output_directory / 'index.html').as_uri()}[/underline cyan]\n")
        else:
            print(f"Successfully built {result.total_documents} documents in {result.elapsed_seconds:.3f}s")
            print(f"Portal entrypoint: {result.output_directory / 'index.html'}")

        return 0
    except Exception as exc:
        if console:
            console.print(f"[bold red]Error building docs:[/bold red] {exc}")
        else:
            print(f"Error building docs: {exc}", file=sys.stderr)
        return 1


def cmd_audit_logs(args: argparse.Namespace) -> int:
    log_file = Path(args.log_file)
    output_html = Path(args.output_html)
    max_records = args.max_records

    if console:
        console.print(f"[bold magenta]>>> Starting Log Audit & Analytics Engine...[/bold magenta]")
        console.print(f"  Log Input  : [cyan]{log_file}[/cyan]")
        console.print(f"  HTML Report: [cyan]{output_html}[/cyan]")
        if max_records:
            console.print(f"  Max Records: [yellow]{max_records}[/yellow]")
        console.print("")
    else:
        print(f">>> Auditing logs: {log_file} -> {output_html}...")

    try:
        engine = LogAnalyticsEngine()
        summary = engine.analyze_file(log_file, max_records=max_records)
        report_path = engine.generate_html_report(summary, output_html)

        if console:
            kpi_table = Table(title="Log Audit Key Metrics", show_header=True, header_style="bold yellow")
            kpi_table.add_column("Metric", style="cyan")
            kpi_table.add_column("Value", style="bold white")

            kpi_table.add_row("Total Scanned Records", f"{summary.total_records:,}")
            kpi_table.add_row("Total Errors (5xx / ERR)", f"[bold red]{summary.error_count + summary.status_5xx:,}[/bold red]")
            kpi_table.add_row("Total Warnings (4xx / WARN)", f"[bold yellow]{summary.warning_count + summary.status_4xx:,}[/bold yellow]")
            kpi_table.add_row("Error Rate", f"{summary.error_rate_percent:.2f}%")
            kpi_table.add_row("Peak Traffic Window", f"{summary.peak_hour} ({summary.peak_hour_requests} reqs)")
            kpi_table.add_row("Average Latency", f"{summary.avg_latency_ms:.2f} ms (P95: {summary.p95_latency_ms:.2f} ms)")
            kpi_table.add_row("Execution Engine", f"[bold green]{summary.parsing_engine}[/bold green]")
            kpi_table.add_row("Scan Elapsed Time", f"{summary.execution_time_ms:.2f} ms")

            console.print(kpi_table)

            if summary.top_endpoints:
                ep_table = Table(title="Top 5 Most Requested Endpoints", show_header=True)
                ep_table.add_column("Endpoint", style="cyan")
                ep_table.add_column("Requests", style="bold green", justify="right")
                for ep, count in summary.top_endpoints:
                    ep_table.add_row(ep, str(count))
                console.print(ep_table)

            console.print(f"\n[bold green][SUCCESS] HTML Audit Dashboard generated successfully![/bold green]")
            console.print(f"Open report: [underline cyan]{report_path.as_uri()}[/underline cyan]\n")
        else:
            print(f"Audit completed: {summary.total_records} records analyzed in {summary.execution_time_ms:.2f}ms")
            print(f"Report: {report_path}")

        return 0
    except Exception as exc:
        if console:
            console.print(f"[bold red]Error auditing logs:[/bold red] {exc}")
        else:
            print(f"Error auditing logs: {exc}", file=sys.stderr)
        return 1


def cmd_pipeline(args: argparse.Namespace) -> int:
    print_banner()
    if console:
        console.print("[bold yellow]>>> Executing Full Enterprise Pipeline...[/bold yellow]\n")
    else:
        print(">>> Executing Full Enterprise Pipeline...")

    res_docs = cmd_build_docs(args)
    if res_docs != 0:
        return res_docs

    res_audit = cmd_audit_logs(args)
    if res_audit != 0:
        return res_audit

    if console:
        console.print("[bold green]=======================================================[/bold green]")
        console.print("[bold green][SUCCESS] Enterprise Pipeline Completed Successfully![/bold green]")
        console.print(f"Portal: [underline cyan]{(Path(args.output_dir) / 'index.html').resolve().as_uri()}[/underline cyan]")
        console.print(f"Audit : [underline cyan]{Path(args.output_html).resolve().as_uri()}[/underline cyan]")
        console.print("[bold green]=======================================================[/bold green]\n")

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logpulse",
        description="LogPulse CLI - Enterprise SOP Static Site Generator & Log Audit Engine",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    subparsers.add_parser("status", help="Check C acceleration status and environment diagnostic")

    p_docs = subparsers.add_parser("build-docs", help="Build Markdown SOPs into static HTML portal")
    p_docs.add_argument("--docs-dir", default="docs", help="Source directory containing Markdown SOPs (default: docs)")
    p_docs.add_argument("--output-dir", default="dist/portal", help="Output directory for static site (default: dist/portal)")

    p_audit = subparsers.add_parser("audit-logs", help="Analyze server log file and generate HTML audit dashboard")
    p_audit.add_argument("--log-file", default="sample_logs/server_production.log", help="Path to server log file")
    p_audit.add_argument("--output-html", default="dist/audit/audit_report.html", help="Path for HTML audit dashboard")
    p_audit.add_argument("--max-records", type=int, default=None, help="Limit number of records to parse")

    p_pipe = subparsers.add_parser("pipeline", help="Run end-to-end documentation build and log audit")
    p_pipe.add_argument("--docs-dir", default="docs", help="Source directory containing Markdown SOPs")
    p_pipe.add_argument("--output-dir", default="dist/portal", help="Output directory for static site")
    p_pipe.add_argument("--log-file", default="sample_logs/server_production.log", help="Path to server log file")
    p_pipe.add_argument("--output-html", default="dist/audit/audit_report.html", help="Path for HTML audit dashboard")
    p_pipe.add_argument("--max-records", type=int, default=None, help="Limit number of records to parse")

    return parser


def main() -> int:
    parser = build_parser()
    if len(sys.argv) == 1:
        parser.print_help()
        return 0

    args = parser.parse_args()

    if args.command == "status":
        return cmd_status(args)
    elif args.command == "build-docs":
        return cmd_build_docs(args)
    elif args.command == "audit-logs":
        return cmd_audit_logs(args)
    elif args.command == "pipeline":
        return cmd_pipeline(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
