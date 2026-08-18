#!/bin/sh

# 让用户在项目目录中直接运行：./qc "/完整路径/稿件.docx"
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 "$SCRIPT_DIR/qc.py" "$@"
