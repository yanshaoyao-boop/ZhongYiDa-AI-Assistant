# 2026-04-01 云端发布经验沉淀

## 目的

这份文档记录 2026-04-01 这次主站成功上线的完整经验，重点避免下次再重复踩以下坑：

- 本机能手动登录服务器，但 Codex 无法直接接管
- 旧系统脚本强制构建所有子工具，导致主站发布被无关工具卡死
- 发布完成与否没有明确验收标准

## 一、这次成功上线的关键结论

### 1. GitHub 代码已经是最新

- 主站成功上线的提交为：`1f23328`
- 这是本次修复报价表格、聊天渲染、编号重复、通知红点的版本

### 2. 云端真正可复用的前提不是“能登录”，而是“Codex 可免密登录”

这次最重要的经验是：

- 用户自己能在第三方 SSH 工具里登录服务器，不代表 Codex 这边也能直接管理云端
- 只有当 Windows 本机标准 SSH 可以免密登录服务器，Codex 才能稳定接手部署、查日志、重启服务

### 3. 旧系统部署脚本不能直接用于主站快速发布

服务器上的系统脚本：

- `/srv/xiaoyi/bin/deploy_from_github.sh`

存在一个关键问题：

- 它会无条件构建 `智能工具源代码` 里的所有子工具
- 即使只想更新主站，也会被某个子工具的构建错误拦住

本次卡住的具体工具是：

- `fba-tool-pro`

错误为：

- `src/core/Generator.ts(112,43): error TS2538`
- `src/core/Generator.ts(113,43): error TS2538`
- `src/core/Generator.ts(114,43): error TS2538`

结论：

- 这份旧脚本不适合当前“主站优先”的发布需求

## 二、云端接管的正确做法

### 1. 使用单独的无口令部署 key

不要依赖有 passphrase 的旧私钥，也不要依赖 Windows `ssh-agent`。

本次最终打通的方式是新建一把无口令专用 key：

```powershell
ssh-keygen -t ed25519 -f $env:USERPROFILE\.ssh\id_ed25519_zyd_codex
```

生成时：

- `Enter passphrase` 直接回车
- `Enter same passphrase again` 再回车

### 2. 将新公钥加入服务器

把以下文件内容追加到服务器：

- `C:\Users\Sawyer Yan\.ssh\id_ed25519_zyd_codex.pub`

服务器操作：

```bash
mkdir -p /root/.ssh
chmod 700 /root/.ssh
nano /root/.ssh/authorized_keys
chmod 600 /root/.ssh/authorized_keys
```

说明：

- 可以保留旧 key
- 新 key 另起一行追加即可

### 3. 免密验证标准

本机必须能直接执行：

```powershell
ssh -o BatchMode=yes -o ConnectTimeout=15 -i "$env:USERPROFILE\.ssh\id_ed25519_zyd_codex" root@47.121.28.135 "hostname && whoami && pwd"
```

成功标准：

- 返回主机名
- 返回 `root`
- 返回 `/root`
- 不再要求输入密码或 passphrase

只有达到这个状态，Codex 才算真正具备云端接管能力。

## 三、这次实际验证出的脚本差异

### 1. 系统脚本

路径：

- `/srv/xiaoyi/bin/deploy_from_github.sh`

特点：

- 无条件执行子工具构建
- 不支持跳过子工具

### 2. 仓库脚本

路径：

- `/var/www/zyd-bot/scripts/deploy/deploy_from_github.sh`

特点：

- 支持 `ENABLE_SUBTOOL_BUILD`
- 默认 `ENABLE_SUBTOOL_BUILD=0`
- 支持跳过子工具构建

但要注意：

- 仓库脚本当前还有一个顺序上的小风险点
- 它在“检查工作区干净”前就会写 `.last_deployed_commit`
- 这会导致 `git status --porcelain` 变脏，存在误伤发布的可能

结论：

- 短期内最稳妥的主站上线方式，仍然是手工主站发布链路
- 后续应单独修正系统脚本或替换为仓库脚本

## 四、当前推荐的主站发布方式

### 适用场景

只更新小易主站，不要求同步构建所有智能工具子项目。

### 正确发布步骤

在本机通过免密 SSH 将以下脚本内容送到服务器执行：

```bash
set -euo pipefail
cd /var/www/zyd-bot
git fetch origin main
git pull --ff-only origin main

cd backend
if [ -d venv ]; then . venv/bin/activate; fi
pip install -r requirements.txt

cd ../frontend
npm install
npm run build

sudo systemctl restart zyd-bot
sudo nginx -t
sudo systemctl reload nginx
sleep 3

cd /var/www/zyd-bot
git rev-parse --short HEAD
systemctl is-active zyd-bot
curl -s http://127.0.0.1:8000/
curl -kIs https://127.0.0.1/ | head -n 1
```

### 为什么这样最稳

- 只更新主站必要内容
- 避开无关子工具构建失败
- 不依赖旧系统脚本的历史逻辑
- 每次发布都有明确验收输出

## 五、主站成功上线的验收标准

本次已验证通过的验收结果如下：

- `COMMIT=1f23328`
- `SERVICE=active`
- `BACKEND={"message":"ZhongYiDa AI Assistant API is running"}`
- `FRONTEND=HTTP/1.1 200 OK`

以后只要这四项同时满足，就可以判断主站已成功更新。

## 六、下次发布的推荐顺序

### 标准顺序

1. 本地代码通过必要测试
2. 推送到 GitHub `origin/main`
3. 确认免密 SSH 通道可用
4. 走“主站手工发布链路”
5. 记录上线 commit
6. 做前后端健康检查

### 不要再走的路径

- 不要默认使用 `/srv/xiaoyi/bin/deploy_from_github.sh` 做主站快速发布
- 不要把“第三方 SSH 工具里能登录”误当成“Codex 也能接管”
- 不要只看构建日志，不做 `systemctl` 和 `curl` 验收

## 七、建议的后续改进

### P1

- 修正 `/srv/xiaoyi/bin/deploy_from_github.sh`，支持显式跳过子工具构建

### P1

- 修正仓库脚本中 `.last_deployed_commit` 和工作区干净校验的顺序

### P2

- 为主站发布做一个专门的“只发主站”脚本，避免人工重复拼装命令

## 八、关键信息速查

- 服务器 IP：`47.121.28.135`
- 服务器用户：`root`
- 项目目录：`/var/www/zyd-bot`
- 服务名：`zyd-bot`
- 免密部署私钥：`C:\Users\Sawyer Yan\.ssh\id_ed25519_zyd_codex`
- 主站成功上线 commit：`1f23328`

