#!/bin/bash
# /srv/xiaoyi/bin/rollback_to_previous.sh
# 小易智能助手 - 回滚到上一个部署版本脚本

set -e

PROJECT_ROOT="/var/www/zyd-bot"
BACKUP_SCRIPT="/srv/xiaoyi/bin/backup.sh"
SERVICE_NAME="zyd-bot"
LAST_COMMIT_FILE="${PROJECT_ROOT}/.last_deployed_commit"

echo ">>> [1/7] 开始回滚流程..."

# 1. 备份
echo ">>> [2/7] 正在执行系统备份..."
if [ -f "$BACKUP_SCRIPT" ]; then
    bash "$BACKUP_SCRIPT"
fi

# 2. 读取上一次 Commit
if [ ! -f "$LAST_COMMIT_FILE" ]; then
    echo "错误: 未找到回滚点记录 $LAST_COMMIT_FILE。"
    exit 1
fi
LAST_COMMIT=$(cat "$LAST_COMMIT_FILE")

# 3. 回滚代码
echo ">>> [3/7] 正在将代码回退到 $LAST_COMMIT..."
cd "$PROJECT_ROOT"
git checkout main
git reset --hard "$LAST_COMMIT"

# 4. 恢复依赖 (如有必要)
echo ">>> [4/7] 正在检查依赖..."
cd "${PROJECT_ROOT}/backend"
if [ -d "venv" ]; then
    source venv/bin/activate
fi
pip install -r requirements.txt

# 5. 重建前端 (如有必要)
echo ">>> [5/7] 正在重建前端..."
cd "${PROJECT_ROOT}/frontend"
npm install
npm run build

# 6. 重启服务
echo ">>> [6/7] 正在重启服务 $SERVICE_NAME..."
sudo systemctl restart "$SERVICE_NAME"

# 7. 健康检查
echo ">>> [7/7] 正在进行健康检查..."
sleep 3
BACKEND_HEALTH=$(curl -s http://127.0.0.1:8000/)
FRONTEND_HEALTH=$(curl -kIs https://127.0.0.1/ | head -n 1) || true

echo "后端检查 (8000): $BACKEND_HEALTH"
echo "前端检查 (HTTPS): $FRONTEND_HEALTH"

echo "=========================================="
echo "回滚完成！当前版本: $(git rev-parse --short HEAD)"
echo "=========================================="
