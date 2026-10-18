#!/usr/bin/env bash
set -euo pipefail

BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
CYAN="\033[0;36m"
RED="\033[0;31m"
RESET="\033[0m"

PYTHON_BIN=""
if command -v python3 &>/dev/null; then
    PYTHON_BIN="python3"
elif command -v python &>/dev/null; then
    PYTHON_BIN="python"
else
    echo -e "${RED}[ERROR] Python 3.9+ is required.${RESET}"
    exit 1
fi

CC_BIN=""
if command -v gcc &>/dev/null; then
    CC_BIN="gcc"
elif command -v clang &>/dev/null; then
    CC_BIN="clang"
fi

if [ -n "$CC_BIN" ]; then
    mkdir -p src/c_modules
    $CC_BIN -O3 -Wall -Wextra -fPIC -shared -o src/c_modules/liblogparser.so src/c_modules/log_parser.c
fi

HAS_PIP=true
if ! $PYTHON_BIN -m pip --version &>/dev/null; then
    HAS_PIP=false
fi

HAS_DEPS=true
if ! $PYTHON_BIN -c "import jinja2, rich, markdown_it, yaml" &>/dev/null; then
    HAS_DEPS=false
fi

if [ "$HAS_PIP" = true ]; then
    $PYTHON_BIN -m pip install -r requirements.txt 2>/dev/null || $PYTHON_BIN -m pip install -r requirements.txt --break-system-packages 2>/dev/null || true
    $PYTHON_BIN -m pip install -e . 2>/dev/null || $PYTHON_BIN -m pip install -e . --break-system-packages 2>/dev/null || true
elif [ "$HAS_DEPS" = false ]; then
    echo -e "${YELLOW}Missing packages. Run: sudo apt update && sudo apt install -y python3-pip python3-venv${RESET}"
fi

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

if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    export PATH="$HOME/.local/bin:$PATH"
fi

cd "$PROJECT_DIR"
$PYTHON_BIN -m src.core.cli status
