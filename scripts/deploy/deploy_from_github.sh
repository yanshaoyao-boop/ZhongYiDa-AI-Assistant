#!/bin/bash
# /srv/xiaoyi/bin/deploy_from_github.sh
# 小易智能助手 - 从 GitHub 自动部署脚本

set -e # 遇到错误立即停止

# 配置变量
PROJECT_ROOT="/var/www/zyd-bot"
BACKUP_SCRIPT="/srv/xiaoyi/bin/backup.sh"
SERVICE_NAME="zyd-bot"
ENV_FILE="${PROJECT_ROOT}/backend/.env"
DB_FILE="${PROJECT_ROOT}/backend/data/prod.db"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo ">>> [1/11] 开始部署流程 ($TIMESTAMP)..."

# 1. 执行现有备份脚本
echo ">>> [2/11] 正在执行系统备份..."
if [ -f "$BACKUP_SCRIPT" ]; then
    bash "$BACKUP_SCRIPT"
else
    echo "警告: 备份脚本 $BACKUP_SCRIPT 未找到，跳过系统备份。"
fi

# 2. 核心私有文件快照
echo ">>> [3/11] 为核心私有文件创建快照..."
mkdir -p "${PROJECT_ROOT}/backend/data/snapshots"
[ -f "$ENV_FILE" ] && cp "$ENV_FILE" "${PROJECT_ROOT}/backend/data/snapshots/.env.${TIMESTAMP}.bak"
[ -f "$DB_FILE" ] && cp "$DB_FILE" "${PROJECT_ROOT}/backend/data/snapshots/prod.db.${TIMESTAMP}.bak"

# 3. 记录当前 Git Commit，用于回滚
cd "$PROJECT_ROOT"
CURRENT_COMMIT=$(git rev-parse HEAD)
echo "$CURRENT_COMMIT" > "${PROJECT_ROOT}/.last_deployed_commit"
echo ">>> [4/11] 当前 Commit: $CURRENT_COMMIT 已记录。"

# 4. Git Fetch & Pull
echo ">>> [5/11] 正在从 GitHub 获取代码 (main 分支)..."
git fetch origin main

# 尝试 fast-forward pull
if ! git pull --ff-only origin main; then
    echo "错误: git pull 失败！检测到服务器端有手动代码改动，请先清理或保存手动冲突。"
    echo "部署已终止。线上应用未受影响。"
    exit 1
fi

# 5. 安装/更新后端依赖
echo ">>> [6/11] 正在安装后端依赖..."
cd "${PROJECT_ROOT}/backend"
# 假设使用 venv
if [ -d "venv" ]; then
    source venv/bin/activate
    pip install -r requirements.txt
else
    pip install -r requirements.txt
fi

# 6. 构建前端
echo ">>> [7/11] 正在构建前端..."
cd "${PROJECT_ROOT}/frontend"
npm install
npm run build

# 7. 重启后端服务
echo ">>> [8/11] 正在重启服务 $SERVICE_NAME..."
sudo systemctl restart "$SERVICE_NAME"

# 8. 检查 Nginx 配置
echo ">>> [9/11] 正在检查 Nginx 配置..."
sudo nginx -t

# 9. 重载 Nginx
echo ">>> [10/11] 正在重载 Nginx..."
sudo systemctl reload nginx

# 10. 健康检查
echo ">>> [11/11] 正在进行系统健康检查..."
sleep 3
BACKEND_HEALTH=$(curl -s http://127.0.0.1:8000/)
FRONTEND_HEALTH=$(curl -kIs https://127.0.0.1/ | head -n 1) || true

echo "后端检查 (8000): $BACKEND_HEALTH"
echo "前端检查 (HTTPS): $FRONTEND_HEALTH"

echo "=========================================="
echo "部署完成！当前版本: $(git rev-parse --short HEAD)"
echo "完成时间: $(date)"
echo "=========================================="
