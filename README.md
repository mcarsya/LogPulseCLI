# LogPulse

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)]()
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)]()
[![C Standard](https://img.shields.io/badge/c-c11-00599C.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()
[![Platform](https://img.shields.io/badge/platform-linux%20%7C%20wsl%20%7C%20macos%20%7C%20windows-lightgrey.svg)]()

**LogPulse** is a lightweight, dual-engine CLI designed for enterprise platform engineering and site reliability teams. It combines an **N-ary Tree Static Site Generator (SSG)** to transform internal Markdown runbooks into responsive offline documentation portals, alongside a **high-throughput log analytics engine** accelerated by native C memory streaming.

---

## Architectural Overview

```
                          ┌───────────────────────────┐
                          │       logpulse CLI        │
                          └─────────────┬─────────────┘
                                        │
                 ┌──────────────────────┴──────────────────────┐
                 │                                             │
                 ▼                                             ▼
     [Static Site Generator]                     [Log Analytics Engine]
  ┌─────────────────────────────┐             ┌─────────────────────────────┐
  │ • Frontmatter YAML Parser   │             │ • Pure Functional Pipeline  │
  │ • N-Ary DocTree AST         │             │   (map, filter, reduce)     │
  │ • DFS (Prev/Next Linking)   │             │ • P50/P95 Latency Percentile│
  │ • BFS (Level-Order Sitemap) │             │ • Time-Series Distribution  │
  │ • Jinja2 Offline Templates  │             └──────────────┬──────────────┘
  └──────────────┬──────────────┘                            │
                 │                                           ▼
                 │                             [Dual-Engine Ingestion]
                 │                           ┌─────────────────────────────┐
                 │                           │ • C Shared Lib (POSIX/Win)  │
                 │                           │   Manual malloc/free chunk  │
                 │                           │ • Transparent Py Fallback   │
                 │                           └──────────────┬──────────────┘
                 ▼                                          ▼
     ┌────────────────────────┐                ┌────────────────────────┐
     │ dist/portal/index.html │                │ dist/audit/report.html │
     │ Responsive Web Portal  │                │ Interactive Dashboard  │
     └────────────────────────┘                └────────────────────────┘
```

---

## Key Features

- **Dual-Engine Execution**:
  - **Native C Layer (`log_parser.c`)**: Chunked streaming I/O (64 KB buffers) with explicit `malloc` and `free` routines, avoiding memory ballooning when parsing large access logs.
  - **Python Fallback**: Automatic, zero-crash fallback to pure Python streaming if a native C compiler is unavailable.
- **N-ary Tree Static Site Generator**:
  - Automatically derives sitemaps and sidebar hierarchies directly from the filesystem structure.
  - Generates pre-order traversal sequences for sequential document reading (Previous / Next navigation).
  - Upward parent pointer resolution generates dynamic breadcrumb paths.
- **Functional Analytics Pipeline**:
  - Immutable data modeling using frozen dataclasses (`LogRecord`, `AuditSummary`).
  - Strict side-effect-free data transformation using function composition (`compose`, `pipe`, `curry`).
  - Time-series aggregations, error rate calculations, and P95 latency evaluations using `functools.reduce` and `map`/`filter` pipelines.
- **Offline & Self-Contained Output**:
  - Zero CDN dependencies. All generated static portals and audit dashboards operate fully offline via `file://` URI protocol.

---

## Project Structure

```
.
├── src/
│   ├── core/
│   │   ├── cli.py               # CLI entrypoint and command dispatcher
│   │   ├── c_bridge.py          # ctypes foreign function interface & fallback
│   │   ├── ssg/                 # Static Site Generator package
│   │   │   ├── models.py        # Document, Metadata, and Heading models
│   │   │   ├── tree.py          # N-ary Tree data structure & traversals
│   │   │   ├── parser.py        # Markdown tokenizer & anchor generator
│   │   │   ├── renderer.py      # Template evaluation engine
│   │   │   └── generator.py     # Build pipeline orchestrator
│   │   └── analytics/           # Functional analytics package
│   │       ├── models.py        # Immutable records & metrics
│   │       ├── pure_functions.py# Pure parsers, combinators & predicates
│   │       ├── aggregators.py   # Functional map-reduce reducers
│   │       └── engine.py        # Log analytics executor & HTML builder
│   └── c_modules/               # High-performance C core
│       ├── log_parser.c         # Memory-managed log parsing implementation
│       ├── log_parser.h         # Export definitions & ABI structures
│       └── Makefile             # Shared library compilation rules
├── templates/
│   ├── ssg/                     # Jinja2 documentation layouts
│   ├── audit/                   # Dashboard templates
│   └── assets/                  # Self-contained CSS & client utilities
├── docs/                        # Enterprise SOP markdown repository
├── sample_logs/                 # Test production log data
├── tests/                       # Test suite (Tree, SSG, Analytics, Bridge)
├── scripts/
│   ├── install.sh               # POSIX / WSL automated setup script
│   ├── build.sh                 # Linux build and test runner
│   └── install.ps1              # Windows PowerShell setup script
├── Makefile                     # Top-level build automation
├── requirements.txt             # Runtime dependencies
└── setup.py                     # Python package definition
```

---

## Installation

### Prerequisites

- Python 3.9+
- Optional for C acceleration: GCC, Clang, or MSVC (MinGW on Windows)

### Linux / WSL / macOS

```bash
# Automated install (builds C shared library and registers CLI)
bash scripts/install.sh
```

Alternatively, build manually using `make`:

```bash
make build-c
make install
```

### Windows (PowerShell)

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\install.ps1
```

Or install via standard `pip`:

```bash
pip install -r requirements.txt
pip install -e .
```

---

## CLI Reference

### 1. System Diagnostic

Verify environment status and native C library linkage:

```bash
logpulse status
```

### 2. Build Documentation Portal (SSG)

Compile Markdown runbooks and SOPs into a static web portal:

```bash
logpulse build-docs --docs-dir docs --output-dir dist/portal
```

*Output:* `dist/portal/index.html` and `dist/portal/sitemap.html`.

### 3. Log Audit & Analytics

Analyze server logs and generate an audit report:

```bash
logpulse audit-logs --log-file sample_logs/server_production.log --output-html dist/audit/audit_report.html
```

*Output:* `dist/audit/audit_report.html`.

### 4. End-to-End Pipeline

Execute both documentation generation and log audit in a single run:

```bash
logpulse pipeline
```

---

## C Module Details

The native parser processes arbitrary log sizes via streaming chunk buffers, bypassing memory limitations:

```c
LogStats* stats = (LogStats*)calloc(1, sizeof(LogStats));
char* chunk_buf = (char*)malloc(CHUNK_BUFFER_SIZE);
char* line_buf = (char*)malloc(line_cap);

// Stream processing loop...

free(line_buf);
free(chunk_buf);
free_log_stats(stats);
```

### Manual Compilation

- **Linux / WSL**:
  ```bash
  gcc -O3 -Wall -Wextra -fPIC -shared -o src/c_modules/liblogparser.so src/c_modules/log_parser.c
  ```
- **macOS**:
  ```bash
  clang -O3 -Wall -Wextra -fPIC -shared -o src/c_modules/liblogparser.dylib src/c_modules/log_parser.c
  ```
- **Windows (MinGW)**:
  ```bash
  gcc -O3 -shared -DBUILDING_LOGPARSER_DLL -o src/c_modules/logparser.dll src/c_modules/log_parser.c
  ```

---

## Testing

Run the test suite:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

Test coverage includes:
- `test_tree.py`: N-ary Tree path synthesis, DFS pre/post-order, BFS level-order, breadcrumbs.
- `test_ssg.py`: Markdown parsing, YAML frontmatter, anchor slugs, alert callouts.
- `test_functional_analytics.py`: Function composition, pure predicates, frequency reduction, latency percentiles.
- `test_c_bridge.py`: Dynamic loading, fallback mechanism, ABI struct mapping.

---

## License

This project is licensed under the MIT License.
# LogPulseCLI
