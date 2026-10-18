# ⚡ LogPulse CLI

> **Enterprise SOP Static Site Generator & Memory-Managed Log Audit Engine**  
> *Combining Python, C (Manual Memory Management), Linux, Git, OOP, Functional Programming, and Data Structures & Algorithms.*

---

## 📋 Daftar Isi

1. [Ringkasan & Tujuan Proyek](#-ringkasan--tujuan-proyek)
2. [Arsitektur Sistem & Spesifikasi Teknis](#-arsitektur-sistem--spesifikasi-teknis)
   - [1. Multi-Language Module (Python & C Memory Management)](#1-multi-language-module-python--c-memory-management)
   - [2. Static Site Generator (OOP & Data Structures)](#2-static-site-generator-oop--data-structures)
   - [3. Log Audit & Analytics Engine (Functional Programming)](#3-log-audit--analytics-engine-functional-programming)
3. [Struktur Direktori Proyek](#-struktur-direktori-proyek)
4. [Instalasi & Otomatisasi](#-instalasi--otomatisasi)
   - [Linux / macOS (Bash)](#opsi-a-linux--macos-bash)
   - [Windows (PowerShell / Command Prompt)](#opsi-b-windows-powershell)
   - [Makefile Automation](#opsi-c-menggunakan-makefile)
5. [Panduan Penggunaan CLI](#-panduan-penggunaan-cli)
6. [Kompilasi Modul C (Manual Memory Management)](#-kompilasi-modul-c-manual-memory-management)
7. [Pengujian Unit (Unit Testing)](#-pengujian-unit-unit-testing)
8. [Lisensi & Kontribusi](#-lisensi--kontribusi)

---

## 📌 Ringkasan & Tujuan Proyek

**LogPulse CLI** adalah alat command-line interface (CLI) internal berskala enterprise yang dirancang untuk kebutuhan tim DevOps, SRE, dan Platform Engineering:
1. **Static Site Generator (SSG) untuk Dokumentasi & SOP**: Mengubah dokumen SOP/Runbook berformat Markdown (`.md`) menjadi portal web statis yang bersih, responsif, memiliki fitur pencarian luring (offline), serta hierarki navigasi otomatis.
2. **Log Audit & Analytics Dashboard**: Menganalisis log server berukuran besar secara cepat, mendeteksi pola lonjakan error/warning, mengagregasi lalu lintas berdasarkan stempel waktu (time-series), dan menyajikan laporan audit ke dalam dasbor HTML statis modern tanpa ketergantungan CDN eksternal.

---

## 🏛️ Arsitektur Sistem & Spesifikasi Teknis

```mermaid
graph TD
    subgraph CLI Entrypoint
        CLI[LogPulse CLI - src/core/cli.py]
    end

    subgraph Module 1: Multi-Language & C Bridge
        C_SRC[log_parser.c / log_parser.h<br/>Manual malloc/free] -->|Compile| C_LIB[liblogparser.so / logparser.dll]
        C_LIB -->|ctypes bridge| BRIDGE[src/core/c_bridge.py]
        BRIDGE -->|Fallback bila belum dikompilasi| PY_STREAM[Python Streaming Parser]
    end

    subgraph Module 2: SSG OOP & Tree DS
        DOCS[docs/*.md SOPs] --> PARSER[MarkdownParser]
        PARSER --> TREE[DocTree - N-Ary Tree Data Structure]
        TREE -->|DFS Pre-Order| LINKS[Prev/Next Document Linking]
        TREE -->|Upward Parent Traversal| CRUMBS[Breadcrumbs Resolution]
        TREE -->|BFS Level-Order| SITEMAP[Automated Sitemap Hierarchy]
        LINKS --> RENDERER[TemplateRenderer - Jinja2]
        CRUMBS --> RENDERER
        SITEMAP --> RENDERER
        RENDERER --> PORTAL[dist/portal/index.html & SOP Pages]
    end

    subgraph Module 3: Functional Analytics
        LOGS[sample_logs/server_production.log] --> PURE_PARSE[Pure Functions: parse_log_line]
        PURE_PARSE --> IMMUTABLE[Immutable LogRecord dataclass]
        IMMUTABLE --> FP_PIPE[Functional Pipeline: map, filter, reduce]
        FP_PIPE --> AGG[build_audit_summary & Hourly Series]
        AGG --> AUDIT_HTML[dist/audit/audit_report.html Dashboard]
    end

    CLI -->|build-docs| Module 2
    CLI -->|audit-logs| Module 3
    CLI -->|status| BRIDGE
    CLI -->|pipeline| Module 2 & Module 3
```

---

### 1. Multi-Language Module (Python & C Memory Management)

- **Modul Python (`src/core/`)**:
  Mengelola CLI interface, argument parser (`argparse`), terminal formatting tingkat enterprise (`rich`), orkestrasi SSG, dan rendering HTML.
- **Modul C (`src/c_modules/log_parser.c`)**:
  - Ditulis dalam C standar dengan **alokasi memori manual murni**:
    - `malloc()` dan `calloc()` untuk alokasi dynamic buffer chunk (64 KB) dan struct statistik `LogStats`.
    - `realloc()` untuk ekspansi dinamis line buffer tanpa risiko buffer overflow.
    - `free()` melalui fungsi C eksplisit `free_log_stats()` guna menjamin **zero memory leak**.
  - **C Bridge (`src/core/c_bridge.py`)**:
    Menghubungkan C shared library melalui Python `ctypes`. Dilengkapi **Transparent Fallback Architecture**: jika pustaka C belum dikompilasi pada sistem target (misal Windows tanpa GCC), LogPulse otomatis beralih ke streaming pure Python parser tanpa crash.

---

### 2. Static Site Generator (OOP & Data Structures)

- **Object-Oriented Programming (OOP)**:
  - `Document`: Enkapsulasi konten Markdown, HTML ter-render, metadata frontmatter, slug, dan breadcrumbs.
  - `DocumentMetadata`: Model metadata dokumen (title, author, version, category, tags, status badge).
  - `MarkdownParser`: Ekstraksi frontmatter YAML, pembuatan anchor deep-linking (`#heading`), dan transformasi callout alert enterprise (`> [!NOTE]`, `> [!WARNING]`, dsb).
  - `TemplateRenderer`: Manajemen template Jinja2, filter format tanggal, dan badge status.
  - `StaticSiteGenerator`: Orkestrator pembangun portal statis.
- **Data Structures & Algorithms (DSA)**:
  - **N-Ary Tree (`DocTree` & `DocTreeNode`)**: Memodelkan struktur direktori folder dan file dokumen sebagai node pohon dengan penunjuk `parent` dan kumpulan `children`.
  - **Depth-First Search (DFS) Pre-Order**: Membangun urutan baca dokumen (Prev/Next navigation chain) dan sitemap.
  - **Breadth-First Search (BFS) Level-Order**: Menggunakan antrean FIFO (`collections.deque`) untuk analisis kedalaman hierarki kategori.
  - **Parent Traversal Algorithm**: Menelusuri penunjuk parent ke arah root untuk meresolusi tautan breadcrumb secara otomatis.

---

### 3. Log Audit & Analytics Engine (Functional Programming)

- **Functional Programming (FP) Paradigm**:
  - **Pure Functions**: Fungsi murni tanpa efek samping (`parse_log_line`, `extract_client_ip`, `extract_endpoint`, `extract_status_code`).
  - **Immutabilitas**: Menggunakan immutable frozen dataclasses (`LogRecord`, `HourlyMetric`, `AuditSummary`).
  - **Higher-Order Functions & Currying**: `compose(*fns)`, `pipe(x, *fns)`, dan fungsi predikat currying `is_status_range(min, max)` serta `is_level(target)`.
  - **Map, Filter, Reduce**:
    - `filter(is_error, records)` & `filter(is_status_range(500, 599), records)`.
    - `map(extract_client_ip, records)`.
    - `functools.reduce(frequency_reducer, items, {})` untuk penghitungan frekuensi kemunculan.
  - **Time-Series Analysis**: Mengagregasi volume lalu lintas, error rate, dan rata-rata latensi (P50 dan P95 percentile) ke dalam rentang waktu per jam.
  - **HTML Audit Dashboard**: Menghasilkan dasbor HTML statis responsif dengan kartu KPI metrik, diagram batang CSS murni, tabel top endpoints, dan tabel analisis insiden error.

---

## 📂 Struktur Direktori Proyek

```
LogPulse-CLI/
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── cli.py                     # CLI entrypoint (rich interface)
│   │   ├── c_bridge.py                # ctypes interface & fallback engine
│   │   ├── ssg/                       # Modul Static Site Generator (OOP)
│   │   │   ├── __init__.py
│   │   │   ├── models.py              # Document, Metadata, Heading, Breadcrumb
│   │   │   ├── tree.py                # N-ary Tree DS & BFS/DFS algorithms
│   │   │   ├── parser.py              # Markdown & Frontmatter parser
│   │   │   ├── renderer.py            # Jinja2 template renderer
│   │   │   └── generator.py           # SSG Orchestrator
│   │   └── analytics/                 # Modul Log Analytics (Functional)
│   │       ├── __init__.py
│   │       ├── models.py              # Immutable LogRecord & AuditSummary
│   │       ├── pure_functions.py      # Pure parsers, combinators, currying
│   │       ├── aggregators.py         # map, filter, functools.reduce
│   │       └── engine.py              # Analytics engine & report builder
│   └── c_modules/                     # Modul Native C
│       ├── log_parser.c               # Implementasi C dengan manual malloc/free
│       ├── log_parser.h               # Header C & struct definisi
│       └── Makefile                   # Kompilasi shared library (.so / .dll)
├── templates/
│   ├── ssg/
│   │   ├── base.html                  # Base layout dokumen SOP
│   │   ├── doc.html                   # Halaman isi SOP & pagination
│   │   └── sitemap.html               # Halaman sitemap hierarki pohon
│   ├── audit/
│   │   └── dashboard.html             # Dasbor laporan audit log
│   └── assets/
│       ├── style.css                  # CSS enterprise mandiri (tanpa CDN)
│       └── app.js                     # Script filter pencarian & copy kode
├── docs/                              # Dokumen SOP internal Markdown
│   ├── index.md                       # Beranda portal SOP
│   ├── devops/
│   │   ├── kubernetes-incident-runbook.md
│   │   └── ci-cd-security-policy.md
│   └── database/
│       ├── postgres-failover-sop.md
│       └── redis-cluster-recovery.md
├── sample_logs/
│   └── server_production.log          # File log server 3.000 baris realistis
├── tests/                             # Unit Test Suite
│   ├── __init__.py
│   ├── test_tree.py                   # Pengujian Tree DS & DFS/BFS
│   ├── test_ssg.py                    # Pengujian OOP SSG & Markdown
│   ├── test_functional_analytics.py   # Pengujian pure functions, map, filter, reduce
│   └── test_c_bridge.py               # Pengujian bridge & fallback
├── scripts/
│   ├── install.sh                     # Script otomatisasi instalasi Linux
│   ├── build.sh                       # Script build & test Linux
│   └── install.ps1                    # Script otomatisasi instalasi Windows
├── Makefile                           # Top-level Makefile
├── requirements.txt                   # Dependensi Python
├── setup.py                           # Konfigurasi pip package
├── .gitignore                         # Aturan Git ignore
└── README.md                          # Dokumentasi teknis proyek
```

---

## 🚀 Instalasi & Otomatisasi

### Opsi A: Linux / macOS (Bash)

Script otomatis akan mendeteksi Python, mengompilasi modul C menjadi `liblogparser.so`, menginstal dependensi, dan meregistrasikan command `logpulse`:

```bash
chmod +x scripts/install.sh scripts/build.sh
./scripts/install.sh
```

### Opsi B: Windows (PowerShell)

Jalankan script PowerShell berikut:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\install.ps1
```

Atau instal secara manual dengan `pip`:

```bash
pip install -r requirements.txt
pip install -e .
```

### Opsi C: Menggunakan Makefile

```bash
# Kompilasi C, jalankan unit test, dan bangun pipeline lengkap
make all

# Atau jalankan target secara spesifik:
make build-c      # Kompilasi pustaka C
make test         # Menjalankan unit test
make build-docs   # Membangun portal web SOP
make audit-logs   # Menganalisis log dan membuat HTML dashboard
make pipeline     # Menjalankan SSG dan Log Audit sekaligus
make clean        # Membersihkan artifact
```

---

## 💻 Panduan Penggunaan CLI

Setelah terinstal, perintah `logpulse` dapat dipanggil langsung dari terminal Anda:

### 1. Memeriksa Status Sistem & Akselerasi C

```bash
logpulse status
```
*Output menampilkan status runtime Python, status linking pustaka akselerasi C, dan kesiapan arsitektur.*

---

### 2. Membangun Portal Dokumentasi SOP (SSG)

```bash
logpulse build-docs --docs-dir docs --output-dir dist/portal
```
- Membaca semua file SOP Markdown di dalam direktori `docs/`.
- Membangun N-ary Tree dan meresolusi breadcrumbs & pagination link.
- Menghasilkan website HTML statis lengkap di `dist/portal/index.html`.

---

### 3. Menganalisis Log Server & Membuat Dasbor Audit

```bash
logpulse audit-logs --log-file sample_logs/server_production.log --output-html dist/audit/audit_report.html
```
- Menjalankan streaming parser terakselerasi C (atau Python fallback).
- Menerapkan functional filtering dan time-series map-reduce.
- Menghasilkan dasbor audit interaktif di `dist/audit/audit_report.html`.

---

### 4. Menjalankan Pipeline Lengkap (End-to-End)

```bash
logpulse pipeline
```
Menjalankan kompilasi portal dokumentasi SOP sekaligus audit log server dalam satu langkah terotomatisasi.

---

## ⚙️ Kompilasi Modul C (Manual Memory Management)

Modul C mengimplementasikan pemindaian cepat berbasis streaming chunk tanpa membaca seluruh file ke dalam RAM:

```c
// Contoh fungsi C dengan manual memory management di src/c_modules/log_parser.c
LogStats* stats = (LogStats*)calloc(1, sizeof(LogStats));
char* chunk_buf = (char*)malloc(CHUNK_BUFFER_SIZE);
char* line_buf = (char*)malloc(line_cap);

// ... streaming loop & line processing ...

free(line_buf);
free(chunk_buf);
// struct stats dilepaskan melalui:
free_log_stats(stats);
```

Untuk mengompilasi secara manual:
- **Linux (GCC)**:
  ```bash
  gcc -O3 -Wall -Wextra -fPIC -shared -o src/c_modules/liblogparser.so src/c_modules/log_parser.c
  ```
- **macOS (Clang)**:
  ```bash
  clang -O3 -Wall -Wextra -fPIC -shared -o src/c_modules/liblogparser.dylib src/c_modules/log_parser.c
  ```
- **Windows (MinGW GCC)**:
  ```bash
  gcc -O3 -shared -DBUILDING_LOGPARSER_DLL -o src/c_modules/logparser.dll src/c_modules/log_parser.c
  ```

---

## 🧪 Pengujian Unit (Unit Testing)

Seluruh komponen memiliki cakupan pengujian unit yang lengkap menggunakan `unittest`:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

Hasil pengujian mencakup:
- `test_tree.py`: N-ary Tree insertion, BFS level-order, DFS pre-order, breadcrumb upward traversal, sequential linking.
- `test_ssg.py`: Markdown parsing, frontmatter YAML extraction, anchor generation, alert callout transformation.
- `test_functional_analytics.py`: Function composition (`compose`, `pipe`), pure predicates, frequency reduce, percentile P50/P95.
- `test_c_bridge.py`: Dynamic shared library loading & transparent fallback validation.

---

## 📄 Lisensi & Standar Rekayasa

Proyek ini dibangun mengikuti kaidah rekayasa perangkat lunak enterprise:
- **Clean Architecture & Separation of Concerns**
- **Type Hinting (PEP 484) & Dataclasses**
- **Zero Memory Leaks pada C**
- **Zero Side-Effects pada Functional Pipeline**
- **Offline Self-Contained Web Output**
