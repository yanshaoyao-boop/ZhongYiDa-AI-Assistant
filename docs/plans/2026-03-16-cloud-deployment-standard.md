# 仲易达 AI 助手：云端部署标准化方案 (中文)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将本地开发的“仲易达 AI 助手”完整部署至阿里云线上服务器，实现公网域名安全访问（HTTPS）。

**Architecture:** 采用经典的 Nginx + PM2 + Python FastAPI 架构。Nginx 负责前端静态资源托管及 HTTPS 卸载，PM2 负责 Python 后端进程守护与日志管理。

**Tech Stack:** Nginx, PM2, Python 3.10+, FastAPI, Vite, SSL (Certbot).

---

### Task 1: 域名解析与基础环境确认 (AliCloud Console & Local)

**Goal:** 确保域名指向服务器，并准备好本地环境。

**Files:**
- Modify: `frontend/.env.production` (新建)
- Modify: `backend/.env` (生产环境配置)

**Step 1: 域名解析**
- 请登录阿里云后台，将 `47.121.28.135` 绑定到你的正式域名（例如 `ai.zhongyida.com`）。

**Step 2: 创建生产环境环境变量**

在 `frontend` 目录下新建 `.env.production`：
```env
VITE_API_BASE_URL=https://[你的域名]/api
```

**Step 3: 提交配置变更**
```bash
git add frontend/.env.production
git commit -m "chore: 添加生产环境前端配置"
```

---

### Task 2: 本地生产环境打包 (Local Command)

**Goal:** 生成轻量化的 `dist` 文件夹，准备上传。

**Files:**
- Create: `deploy_package.sh` (可选，辅助脚本)

**Step 1: 前端打包**
Run: `cd frontend && npm install && npm run build`
Expected: 生成 `frontend/dist` 文件夹。

**Step 2: 确认后端依赖**
Run: `cd backend && pip freeze > requirements.txt` (如果还没更新)
Expected: `requirements.txt` 包含所有必需库。

---

### Task 3: 编写 Nginx 与后端服务配置文件 (Codex/Antigravity)

**Goal:** 准备好服务器所需的配置文件模板。

**Files:**
- Create: `backend/deploy/nginx.conf`
- Create: `backend/deploy/ecosystem.config.js` (PM2 配置)

**Step 1: 编写 Nginx 配置模板**
```nginx
server {
    listen 80;
    server_name [你的域名];
    
    location / {
        root /var/www/zhongyida/frontend;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Step 2: 编写 PM2 启动配置**
```javascript
module.exports = {
  apps: [{
    name: "zhongyida-api",
    script: "python3",
    args: "main.py",
    cwd: "/var/www/zhongyida/backend",
    interpreter: "none",
    env: {
      PORT: "8000",
      PYTHONPATH: "."
    }
  }]
}
```

---

### Task 4: 编写“一键部署脚本” (Antigravity)

**Goal:** 为用户提供一个在服务器上运行的脚本，自动完成安装与重启。

**Files:**
- Create: `server_deploy.sh`

**Step 1: 编写部署自动化逻辑**
脚本功能：
1. 更新代码（Git Pull）。
2. 安装/更新 Python 虚拟环境依赖。
3. 复制静态文件到 `/var/www`。
4. 重启 PM2 进程。
5. 刷新 Nginx 配置。

---

### Task 5: 生产环境上线与安全加固 (Server)

**Goal:** 执行最后的启动命令，开启 HTTPS。

**Step 1: 安装必要软件**
Run: `sudo apt update && sudo apt install nginx python3-venv certbot python3-certbot-nginx -y`

**Step 2: 配置 SSL**
Run: `sudo certbot --nginx -d [你的域名]`

**Step 3: 启动服务**
Run: `pm2 start backend/deploy/ecosystem.config.js`

---

### 🤝 部署守则 (Deployment Rules)

1. **DB 安全**：SQLite 数据库文件 `data/app.db` 必须位于非公开目录。
2. **CORS 严格限制**：后端 `main.py` 必须指明正式域名的 `ALLOWED_ORIGINS`。
3. **备份优先**：每次部署前自动备份原有的 `dist` 文件夹。
