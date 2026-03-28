# 本地与云端隔离规则

这套规则的目标只有一个：**以后本地的数据不会直接跟着代码上传到云端，云端只使用云端自己的配置和数据库。**

## 目录职责

- `backend/`：业务代码目录，可以进入 Git，可以发布到云端。
- `frontend/`：前端源码目录，可以进入 Git；真正上传云端的是构建后的 `dist`。
- `private/`：本地私有目录，只放密钥备忘、临时截图、个人笔记，不进入 Git。
- `archives/`：本地归档目录，只放历史压缩包、临时备份，不进入 Git。
- `release-artifacts/`：本地发布包目录，只放安全发布包，不进入 Git。

## 永远不要上传的内容

- `backend/.env`
- `backend/data/*.db`
- `backend/venv/`
- 任意 `.zip` 归档包
- `private/` 下的所有内容
- `archives/` 下的所有内容

## 以后发布的唯一入口

在本地项目根目录执行：

```powershell
.\scripts\prepare-release.ps1
```

这条命令会自动：

1. 构建前端 `frontend/dist`
2. 只打包允许上云的后端代码
3. 生成两个安全发布包到 `release-artifacts/`
4. 同步智能工具运行资源到 `backend/data/tools`

生成结果：

- `release-artifacts/backend-release.zip`
- `release-artifacts/frontend-release.zip`

以后上传服务器时，只上传这两个包，不再把整个项目目录直接覆盖到云端。

> `backend-release.zip` 现在默认包含智能工具运行所需资源（位于 `backend/data/tools`），
> 云端同步后可直接使用 `/api/tools/runtime/...`。

## 云端自己的数据

云端必须长期保留自己的生产数据，不跟本地代码混放：

- 云端 `.env`
- 云端数据库 `prod.db`
- 云端 Nginx 配置
- 云端 systemd 服务配置

本地修改代码不会自动改掉这些生产数据；只有在服务器上手工改，才会生效。

## 建议的操作习惯

- 本地临时文件，一律放进 `private/` 或 `archives/`
- 发布时，只认 `release-artifacts/`
- 服务器上只更新代码，不覆盖 `.env` 和数据库
- 每次发布前，先备份云端 `.env` 和数据库
