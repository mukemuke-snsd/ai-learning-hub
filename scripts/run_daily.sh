#!/bin/bash
# AI Learning Hub 每日自动任务启动脚本
# 由 launchd 调用，确保环境变量和路径正确

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

# 加载 .env（launchd 不继承 shell 环境变量）
if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

"$PROJECT_DIR/.venv/bin/python3" "$PROJECT_DIR/auto_daily.py" "$@"
