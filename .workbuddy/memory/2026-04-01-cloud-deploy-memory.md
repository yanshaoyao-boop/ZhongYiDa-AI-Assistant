# 2026-04-01 云端接管与主站发布记忆

## 今日结论

- Codex 已具备直接接管云服务器的能力
- 成功方式不是依赖旧的带口令私钥，而是新增一把无口令部署 key
- 主站已通过手工主站发布链路成功上线，线上版本为 `1f23328`

## 这次踩过的坑

### 1. 手动能登录，不等于 Codex 能接管

- 第三方 SSH 工具内部登录成功，不代表当前 Codex 会话也有同样权限
- 必须让 Windows 本机标准 SSH 能免密登录，Codex 才能稳定执行远端命令

### 2. 旧系统部署脚本会强制构建所有子工具

旧脚本：

- `/srv/xiaoyi/bin/deploy_from_github.sh`

问题：

- 一定会扫描并构建 `智能工具源代码`
- 即使主站代码没问题，也会被无关子工具拦住

本次实际拦截项：

- `fba-tool-pro`
- TypeScript 错误 `TS2538`

### 3. `sudo ENABLE_SUBTOOL_BUILD=0 ...` 没有实际绕过旧脚本

原因不是命令写错，而是：

- 旧系统脚本根本没有读取这个变量
- 它内部直接写死了子工具构建逻辑

## 这次正确做法

### 1. 新建无口令部署 key

本机命令：

```powershell
ssh-keygen -t ed25519 -f $env:USERPROFILE\.ssh\id_ed25519_zyd_codex
```

要求：

- passphrase 留空

### 2. 公钥加入服务器

将以下公钥追加到服务器：

- `C:\Users\Sawyer Yan\.ssh\id_ed25519_zyd_codex.pub`

服务器文件：

- `/root/.ssh/authorized_keys`

### 3. 免密检查

必须能通过：

```powershell
ssh -o BatchMode=yes -o ConnectTimeout=15 -i "$env:USERPROFILE\.ssh\id_ed25519_zyd_codex" root@47.121.28.135 "hostname && whoami && pwd"
```

## 主站发布标准流程

只更新主站时，直接做：

1. `git fetch origin main`
2. `git pull --ff-only origin main`
3. 后端 `pip install -r requirements.txt`
4. 前端 `npm install`
5. 前端 `npm run build`
6. `sudo systemctl restart zyd-bot`
7. `sudo nginx -t`
8. `sudo systemctl reload nginx`
9. 健康检查

## 本次上线验收结果

- `COMMIT=1f23328`
- `SERVICE=active`
- `BACKEND={"message":"ZhongYiDa AI Assistant API is running"}`
- `FRONTEND=HTTP/1.1 200 OK`

## 下次优先使用

如果只是发小易主站，不要先跑旧系统脚本，优先按主站手工发布链路执行。

## 后续待补

- 修旧系统脚本的子工具强制构建问题
- 修仓库部署脚本的工作区自检顺序问题
