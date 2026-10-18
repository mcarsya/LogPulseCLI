#!/usr/bin/env bash
# ==============================================================================
# LogPulse CLI - Linux & Unix Automated Installation Script
# Configures C module compilation, virtual environment, and CLI registration.
# ==============================================================================

set -euo pipefail

BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
CYAN="\033[0;36m"
RED="\033[0;31m"
RESET="\033[0m"

echo -e "${BOLD}${CYAN}"
echo "=========================================================="
echo "         LogPulse CLI Enterprise Installer (Linux)        "
echo "=========================================================="
echo -e "${RESET}"

# 1. Detect Python 3.9+
PYTHON_BIN=""
if command -v python3 &>/dev/null; then
    PYTHON_BIN="python3"
elif command -v python &>/dev/null; then
    PYTHON_BIN="python"
else
    echo -e "${RED}[ERROR] Python 3 is not installed. Please install Python 3.9+ first.${RESET}"
    exit 1
fi

PY_VERSION=$($PYTHON_BIN -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
echo -e "${GREEN}[+] Detected Python binary: ${PYTHON_BIN} (v${PY_VERSION})${RESET}"

# 2. Check C Compiler & Build Shared Library
echo -e "\n${CYAN}>>> Checking C Compilation Toolchain...${RESET}"
CC_BIN=""
if command -v gcc &>/dev/null; then
    CC_BIN="gcc"
elif command -v clang &>/dev/null; then
    CC_BIN="clang"
fi

if [ -n "$CC_BIN" ]; then
    echo -e "${GREEN}[+] C compiler detected: ${CC_BIN}${RESET}"
    echo -e "${CYAN}>>> Compiling C acceleration shared library (liblogparser.so)...${RESET}"
    mkdir -p src/c_modules
    $CC_BIN -O3 -Wall -Wextra -fPIC -shared -o src/c_modules/liblogparser.so src/c_modules/log_parser.c
    echo -e "${GREEN}[+] Successfully compiled: src/c_modules/liblogparser.so${RESET}"
else
    echo -e "${YELLOW}[!] No GCC or Clang compiler detected in PATH.${RESET}"
    echo -e "${YELLOW}    LogPulse CLI will operate in High-Performance Python Fallback mode.${RESET}"
fi

# 3. Install Python Dependencies & Package
echo -e "\n${CYAN}>>> Installing Python Dependencies & Registering CLI...${RESET}"
$PYTHON_BIN -m pip install --upgrade pip
$PYTHON_BIN -m pip install -r requirements.txt
$PYTHON_BIN -m pip install -e .

# 4. Verify Installation & Run Diagnostic
echo -e "\n${CYAN}>>> Running LogPulse CLI Self-Test...${RESET}"
$PYTHON_BIN -m src.core.cli status

echo -e "${BOLD}${GREEN}"
echo "=========================================================="
echo "[SUCCESS] LogPulse CLI successfully installed!"
echo "=========================================================="
echo -e "${RESET}"
echo -e "You can now execute commands directly:"
echo -e "  ${CYAN}logpulse status${RESET}         - Inspect C acceleration & diagnostic"
echo -e "  ${CYAN}logpulse build-docs${RESET}     - Build Markdown SOPs to static web portal"
echo -e "  ${CYAN}logpulse audit-logs${RESET}     - Run functional log audit & HTML dashboard"
echo -e "  ${CYAN}logpulse pipeline${RESET}       - Execute end-to-end documentation & audit"
echo ""
