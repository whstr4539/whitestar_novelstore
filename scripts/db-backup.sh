#!/bin/bash
# 数据库备份脚本：docker compose exec postgres pg_dump
# 用法: bash scripts/db-backup.sh [备份文件名前缀]
set -e
cd "$(dirname "$0")/.."

PREFIX=${1:-novel_db}
STAMP=$(date +%Y%m%d_%H%M%S)
OUT="db/backup/${PREFIX}_${STAMP}.sql"

echo "==> 备份到 ${OUT}"
docker exec novel-postgres pg_dump -U novel_user -d novel_db --clean --if-exists > "$OUT"
echo "==> 完成: $(du -h "$OUT" | cut -f1)"
