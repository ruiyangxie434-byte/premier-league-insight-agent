# Windows 本地启动与验收

本文适用于 `v0.13.0 · Similarity Scout`。示例使用 PowerShell；每条命令所在目录都明确写出，避免 `package.json`、虚拟环境或端口问题被误判为代码故障。

## 1. 环境要求

| 软件 | 建议版本 | 验证命令 |
|---|---|---|
| Git | 最新稳定版 | `git --version` |
| Node.js | 22 LTS | `node --version` |
| npm | 随 Node 安装 | `npm --version` |
| Python | 3.12.x | `py -3.12 --version` |
| VS Code | 最新稳定版 | — |

应用使用 SQLite，本地不需要安装 PostgreSQL、MySQL 或其他数据库服务。

## 2. 第一次安装

### 2.1 获取代码

在准备存放项目的目录运行：

```powershell
git clone https://github.com/ruiyangxie434-byte/premier-league-insight-agent.git
cd .\premier-league-insight-agent
```

后续命令中的“项目根目录”就是当前包含 `backend`、`frontend` 和 `README.md` 的目录。

### 2.2 安装后端

在项目根目录运行：

```powershell
cd .\backend
py -3.12 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

命令行开头出现 `(.venv)` 表示虚拟环境已激活。数据库会在首次启动时自动迁移和写入固定快照，无需删除旧库。

### 2.3 安装前端

回到项目根目录后运行：

```powershell
cd ..\frontend
npm ci
Copy-Item .env.example .env.local
```

`.env`、`.env.local`、SQLite 数据库和 `node_modules` 都不应提交到 GitHub。

## 3. 每次启动

需要同时保持两个终端运行。

### 终端 1：后端

从项目根目录运行：

```powershell
cd .\backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app
```

成功标志：

```text
Application startup complete
Uvicorn running on http://127.0.0.1:8000
```

### 终端 2：前端

从项目根目录运行：

```powershell
cd .\frontend
npm run dev
```

成功标志：

```text
Local: http://localhost:3000
Ready
```

然后打开 <http://localhost:3000>。也可以使用 <http://127.0.0.1:3000>；前端会自动选择同名后端地址，开发环境后端同时允许这两个来源。旧 `.env` 中即使只写了 `localhost`，`v0.13.0` 也会补齐本地别名。

## 4. 地址速查

| 用途 | 地址 |
|---|---|
| 前端 | <http://localhost:3000> |
| 后端健康检查 | <http://127.0.0.1:8000/api/health> |
| Swagger API 文档 | <http://127.0.0.1:8000/docs> |
| 球员中心 | <http://localhost:3000/players> |
| League Copilot | <http://localhost:3000/copilot> |

健康检查应包含：

```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "version": "0.13.0"
  }
}
```

Similarity Scout 可以直接用浏览器或 Swagger 验证：

```text
http://127.0.0.1:8000/api/players/bukayo-saka/similar?minimum_minutes=450&limit=5
```

## 5. 常见问题

### `No module named uvicorn`

原因通常是后端虚拟环境没有激活，或终端不在 `backend` 目录。

```powershell
cd .\backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app
```

### `ENOENT ... package.json`

原因是 npm 在项目根目录或 `backend` 目录执行。切换到前端：

```powershell
cd .\frontend
npm run dev
```

如果当前已经在 `backend`，使用：

```powershell
cd ..\frontend
npm run dev
```

### `WinError 10048` 或 8000 端口被占用

先只读确认占用进程：

```powershell
$serverPid = (Get-NetTCPConnection -LocalPort 8000 -State Listen).OwningProcess
Get-Process -Id $serverPid
```

确认它是旧的 Python 后端后再停止：

```powershell
Stop-Process -Id $serverPid
python -m uvicorn app.main:app
```

不要在未确认进程名称时批量结束所有 Python 进程。

### 页面能打开，但显示数据离线

按顺序检查：

1. 打开 `/api/health`，确认后端版本和状态。
2. 确认后端终端没有退出。
3. 强制刷新前端页面（`Ctrl + F5`）。
4. 查看首页“API 地址”，它应与当前浏览器主机名一致。

`v0.13.0` 已兼容 `localhost:3000` 和 `127.0.0.1:3000`，不需要为了跨域问题反复重启项目。

## 6. 完整验收

### 后端

在 `backend` 目录且虚拟环境已激活时运行：

```powershell
python -m pytest
```

当前应显示 `55 passed`。测试覆盖数据快照、迁移、球员分页、Similarity Scout、转会分段、Agent、Copilot 五工具和异常输入。

### 前端

在 `frontend` 目录运行：

```powershell
npm run lint
npx tsc --noEmit
npm run build
```

三个命令都应以退出码 `0` 结束。页面验收重点：

- 首页显示 `v0.13.0 · Similarity Scout`；
- 后端状态显示 `healthy` 和 `0.13.0`；
- 球员详情能切换相似球员分钟门槛；
- 推荐卡能带着指定两名球员进入雷达图；
- 门将详情明确说明专属指标不足，不输出相似排行；
- 手机宽度下没有明显横向溢出。

## 7. Git 检查

在项目根目录运行：

```powershell
git status -sb
git check-ignore frontend\.env.local
git check-ignore backend\.env
git check-ignore backend\pl_geo_analytics.db
```

后三条应输出对应路径，说明密钥、个人配置和本地数据库不会进入提交。

提交或推送前至少完成：

```powershell
git diff --check
git status -sb
```

不要提交真实 API Key、`.env`、SQLite 数据库、`.next` 或 `node_modules`。
