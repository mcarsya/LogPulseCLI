#!/usr/bin/env bash
# ==============================================================================
# LogPulse CLI - Automated Build & Test Runner (Linux / macOS)
# ==============================================================================

set -euo pipefail

CYAN="\033[0;36m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RESET="\033[0m"

echo -e "${CYAN}>>> Step 1: Compiling C Native Shared Library...${RESET}"
if command -v gcc &>/dev/null; then
    gcc -O3 -Wall -Wextra -fPIC -shared -o src/c_modules/liblogparser.so src/c_modules/log_parser.c
    echo -e "${GREEN}[+] Successfully compiled liblogparser.so with gcc${RESET}"
elif command -v clang &>/dev/null; then
    clang -O3 -Wall -Wextra -fPIC -shared -o src/c_modules/liblogparser.so src/c_modules/log_parser.c
    echo -e "${GREEN}[+] Successfully compiled liblogparser.so with clang${RESET}"
else
    echo -e "${YELLOW}[!] Warning: No C compiler found. Skipping C compilation.${RESET}"
fi

echo -e "\n${CYAN}>>> Step 2: Running Unit Test Suite...${RESET}"
python3 -m unittest discover -s tests -p "test_*.py" -v

echo -e "\n${CYAN}>>> Step 3: Executing End-to-End Pipeline...${RESET}"
python3 -m src.core.cli pipeline

echo -e "\n${GREEN}[SUCCESS] All build and pipeline checks passed!${RESET}"
