#!/bin/bash
# 阿里云 ECS (Ubuntu 22.04+) 初始化脚本
# 仅供参考，请根据实际情况以 root 权限执行

set -e

echo "开始安装系统依赖..."
apt update
apt install -y python3 python3-venv python3-pip python3-dev
apt install -y nginx git curl

echo "创建项目目录..."
mkdir -p /var/www/zyd-bot
# 假设您已将代码上传/clone 至 /var/www/zyd-bot

cd /var/www/zyd-bot/backend

echo "创建 Python 虚拟环境..."
python3 -m venv venv
source venv/bin/activate

echo "安装 Python 依赖..."
# 需要确保 backend 下有 requirements.txt
pip install -r requirements.txt
pip install gunicorn uvicorn

echo "安装完成。接下来的建议步骤："
echo "1. 将 deploy/.env.prod 复制为 /var/www/zyd-bot/backend/.env"
echo "2. 将 deploy/bot_api.service 复制到 /etc/systemd/system/zyd-bot.service"
echo "3. 启用服务: systemctl enable zyd-bot && systemctl start zyd-bot"
echo "4. 将 deploy/nginx.conf 的内容复制到 /etc/nginx/sites-available/default (或新建配置并 link)"
echo "5. 测试域名访问: http://zhongyidazhinengzhushou.cn"
echo "6. 重启 Nginx: nginx -s reload"
