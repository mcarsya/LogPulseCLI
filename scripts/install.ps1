$ErrorActionPreference = "Stop"

$pyVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "Python is not installed or not in PATH."
    exit 1
}

$gccPath = Get-Command gcc -ErrorAction SilentlyContinue
if ($gccPath) {
    gcc -O3 -shared -DBUILDING_LOGPARSER_DLL -o src/c_modules/logparser.dll src/c_modules/log_parser.c
}

python -m pip install -r requirements.txt
python -m pip install -e .

logpulse status
