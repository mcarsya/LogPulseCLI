# ==============================================================================
# LogPulse CLI - Windows Automated Setup Script (PowerShell)
# ==============================================================================

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "        LogPulse CLI Enterprise Installer (Windows)       " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Verify Python
$pyVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Python is not installed or not in PATH." -ForegroundColor Red
    exit 1
}
Write-Host "[+] Detected: $pyVersion" -ForegroundColor Green

# 2. Check C Compiler
$gccPath = Get-Command gcc -ErrorAction SilentlyContinue
if ($gccPath) {
    Write-Host "[+] GCC detected. Compiling C acceleration library (logparser.dll)..." -ForegroundColor Green
    gcc -O3 -shared -DBUILDING_LOGPARSER_DLL -o src/c_modules/logparser.dll src/c_modules/log_parser.c
    Write-Host "[+] Compiled: src/c_modules/logparser.dll" -ForegroundColor Green
} else {
    Write-Host "[!] No GCC found in PATH. LogPulse CLI will run in High-Performance Python Fallback Mode." -ForegroundColor Yellow
}

# 3. Install Python Dependencies
Write-Host "`n>>> Installing requirements and registering CLI..." -ForegroundColor Cyan
python -m pip install -r requirements.txt
python -m pip install -e .

# 4. Run System Diagnostic
Write-Host "`n>>> Running LogPulse CLI Diagnostic..." -ForegroundColor Cyan
logpulse status

Write-Host "`n[SUCCESS] LogPulse CLI setup complete!" -ForegroundColor Green
Write-Host "Try running: logpulse pipeline" -ForegroundColor White
