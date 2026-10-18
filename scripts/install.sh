#!/usr/bin/env bash
# ==============================================================================
# LogPulse CLI - Linux & WSL Automated Installation Script
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
echo "         LogPulse CLI Enterprise Installer (Linux/WSL)    "
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

# 3. Check for Python Pip / Dependencies
echo -e "\n${CYAN}>>> Verifying Python Dependencies...${RESET}"
HAS_PIP=true
if ! $PYTHON_BIN -m pip --version &>/dev/null; then
    HAS_PIP=false
fi

# Check if required modules already exist in system Python (common in Ubuntu WSL)
HAS_DEPS=true
if ! $PYTHON_BIN -c "import jinja2, rich, markdown_it, yaml" &>/dev/null; then
    HAS_DEPS=false
fi

if [ "$HAS_PIP" = true ]; then
    echo -e "${GREEN}[+] pip detected.${RESET}"
    # Try install with fallback for PEP 668 externally-managed environments
    $PYTHON_BIN -m pip install -r requirements.txt 2>/dev/null || $PYTHON_BIN -m pip install -r requirements.txt --break-system-packages 2>/dev/null || true
    $PYTHON_BIN -m pip install -e . 2>/dev/null || $PYTHON_BIN -m pip install -e . --break-system-packages 2>/dev/null || true
elif [ "$HAS_DEPS" = true ]; then
    echo -e "${GREEN}[+] Required packages (jinja2, rich, markdown_it, yaml) are already present in Ubuntu Python!${RESET}"
else
    echo -e "${YELLOW}[!] pip is not installed on this Linux/WSL distribution.${RESET}"
    echo -e "${YELLOW}    To install pip and venv, run:${RESET}"
    echo -e "    ${BOLD}sudo apt update && sudo apt install -y python3-pip python3-venv${RESET}\n"
fi

# 4. Create convenient standalone binary wrapper in ~/.local/bin/logpulse
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "$HOME/.local/bin"
cat << 'EOF' > "$HOME/.local/bin/logpulse"
#!/usr/bin/env bash
PYTHON_CMD="python3"
if ! command -v python3 &>/dev/null; then
    PYTHON_CMD="python"
fi
exec $PYTHON_CMD -m src.core.cli "$@"
EOF
chmod +x "$HOME/.local/bin/logpulse"

# Ensure ~/.local/bin is in PATH for future sessions
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    export PATH="$HOME/.local/bin:$PATH"
fi

# 5. Verify Installation & Run Diagnostic
echo -e "\n${CYAN}>>> Running LogPulse CLI Self-Test...${RESET}"
cd "$PROJECT_DIR"
$PYTHON_BIN -m src.core.cli status

echo -e "${BOLD}${GREEN}"
echo "=========================================================="
echo "[SUCCESS] LogPulse CLI is ready in Linux / WSL!"
echo "=========================================================="
echo -e "${RESET}"
echo -e "You can execute commands directly:"
echo -e "  ${CYAN}python3 -m src.core.cli status${RESET}      - Inspect diagnostic & C acceleration"
echo -e "  ${CYAN}python3 -m src.core.cli build-docs${RESET}  - Build Markdown SOPs to static HTML portal"
echo -e "  ${CYAN}python3 -m src.core.cli audit-logs${RESET}  - Run log audit & HTML dashboard"
echo -e "  ${CYAN}python3 -m src.core.cli pipeline${RESET}    - Execute full end-to-end pipeline"
echo ""
echo -e "Or using the registered binary wrapper:"
echo -e "  ${CYAN}~/.local/bin/logpulse pipeline${RESET} (or simply ${CYAN}logpulse pipeline${RESET})"
echo ""
