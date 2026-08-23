#!/bin/bash
# 一键启动后端开发服务器（依赖 Docker 中的 PostgreSQL/Redis）
# 用法: bash scripts/dev-backend.sh
cd "$(dirname "$0")/../backend"

# 检查 Docker 服务
if ! docker ps --format "{{.Names}}" 2>/dev/null | grep -q novel-postgres; then
    echo "!! PostgreSQL/Redis 未运行，先启动: cd .. && docker compose up -d"
    exit 1
fi

# 检查依赖
if [ ! -d .venv ]; then
    echo ">> 创建虚拟环境..."
    python -m venv .venv
    .venv/Scripts/pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
fi

echo ">> 启动 http://localhost:8000/docs  (Ctrl+C 停止)"
exec .venv/Scripts/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
