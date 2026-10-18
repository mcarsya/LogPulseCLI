#!/usr/bin/env bash
set -euo pipefail

if command -v gcc &>/dev/null; then
    gcc -O3 -Wall -Wextra -fPIC -shared -o src/c_modules/liblogparser.so src/c_modules/log_parser.c
elif command -v clang &>/dev/null; then
    clang -O3 -Wall -Wextra -fPIC -shared -o src/c_modules/liblogparser.so src/c_modules/log_parser.c
fi

python3 -m unittest discover -s tests -p "test_*.py" -v
python3 -m src.core.cli pipeline
