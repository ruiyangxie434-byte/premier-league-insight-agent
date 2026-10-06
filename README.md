# 英超智析 Agent | Premier League Insight Agent

> 面向中文英超球迷与内容创作者的垂直足球数据分析助手  
> 将球队、球员与比赛数据转化为可查询、可比较、可解释的分析结论。

**当前版本：`v0.21.0 · Season Archive & Match Centre`**

**项目状态：MVP 开发中**

本次新增多赛季历史、比赛预测、注册登录、足球新闻、实时数据接口与部署配置，并完善球员头像、首页横向对比和移动端布局。完整改动与验收记录见 [v0.21.0 升级说明](docs/UPGRADE_2026_10_06.md)。

历史分析和账户功能可本地运行；实时比赛数据需要后端配置 API-Football Key。仓库已提供 Docker Compose + Caddy 部署配置，尚未部署到公网。

## 项目简介

Premier League Insight Agent 是一个结合足球数据工程、Web 开发与大模型应用的英超数据分析项目。

系统通过数据库查询、每 90 分钟指标计算、证据排序和结论边界判断生成结构化分析。League Copilot 允许通义千问从受控函数清单中选择数据工具；千问不可用时，系统会使用同一工具执行层的本地安全路由。

项目由数据科学与大数据技术专业学生独立开发，主要用于比赛展示、GitHub 项目积累与足球数据分析实践。

历史档案、比赛中心与账户系统独立接入现有平台；原有球员统计和 Copilot 工具继续使用各自标明的赛季范围。

## 当前功能

| 模块 | 已实现能力 |
|---|---|
| 数据库 | 球队、球员、积分榜、比赛、事件、Agent 分析记录、账户与登录会话关系模型 |
| 数据 API | 球队、积分榜、球员、历史比赛事件与分析记录查询接口 |
| 球场地图 | 2024-25 完整 20 队、球场搜索、标记联动与定位动画 |
| 球队详情 | 20 支球队均可从地图进入资料页，并展示该队完整球员赛季记录 |
| 完整积分榜 | 2024-25 最终 20 队积分榜、十列排序、冠军/欧冠/降级标记 |
| 赛季赛果管道 | OpenFootball 固定提交、CC0 许可、380 场解析校验与幂等导入 |
| Season Form Lab | 38 轮积分走势、20 队末五场、主客场拆分与球队 38 场赛果 |
| Season Timeline Lab | 任意轮次完整积分榜、排名升降、四队轨迹、榜首更替与单队赛季故事 |
| 球员数据中心 | 574 条球员—球队记录、搜索、筛选、排序、分页与详情页 |
| 球员定妆照 | 574 条球员赛季记录映射到 562 个球员身份；兼容新旧 API 图片字段，主图失败或超时尝试备用来源，最终显示轮廓与姓名缩写 |
| 首页工作台 | 球员、球队、赛季、AI 四类功能桌面四列、平板两列、手机横向滑动；增加历史、比赛中心和账户入口 |
| 多赛季历史 | 2021-22 至 2026-27 六个赛季的赛程、赛果、计算积分榜、球队趋势与场均积分比较 |
| 比赛结果预测 | 历史主客场进失球泊松基线，输出胜平负概率与前三个比分，明确样本要求和训练截止日期 |
| 注册与登录 | 持久化账户、scrypt 密码散列、HttpOnly 会话 Cookie、刷新保持登录、退出撤销、Origin 校验与基础限流 |
| 足球新闻 | BBC Sport 足球 RSS 标题、发布时间和原文链接；包含英超及其他足球赛事 |
| 实时比分与赛程 | API-Football 接口、按日期查赛程、页面内 SSE 比分推送、比赛首发与替补；需配置 Key 并具备对应数据权限 |
| 阵容、转会与伤病 | 按数据源球队 ID 获取现役名单、转会记录和赛季伤病/停赛；按接口周期缓存并标明来源与更新时间 |
| 移动端与部署 | 手机导航、表单与表格适配；Docker Compose + Caddy HTTPS、数据库持久卷、健康检查和同域 API 代理配置 |
| 球员可视化 | 后端统一计算每 90 分钟指标、位置感知百分位与单人/双人雷达图 |
| Similarity Scout | 同位置相似画像、位置权重、最大差异解释与一键双人对比 |
| Evidence Center | 统一核验数据来源、覆盖规模、许可、快照日期与使用边界 |
| Matchup Lab | 任意两队的赛季画像、八维优势矩阵与两回合直接交锋 |
| Squad Lens | 单队位置分钟结构、队内统计领跑者、核心负荷与可调门槛 |
| Transfer Signal | 球队位置基线、优先缺口、外队历史统计候选与权衡项 |
| Club Briefing Room | 汇总赛季、阵容与三条位置观察队列，并支持打印 / 保存 PDF |
| 球员分析 | 双球员比较、四种分析侧重点与 Player Lab 选择联动 |
| 比赛数据管道 | StatsBomb Open Data 清洗脚本、坐标归一化、来源 ID 与幂等导入 |
| Match Lab | Arsenal 4–2 Liverpool 的 28 次射门、xG 对比、筛选、进球时间线与事件清单 |
| Agent 工具链 | 意图识别、数据查询、指标计算、证据排序与结论生成 |
| League Copilot | 积分榜、球队状态、赛季时间轴、球队简报、阵容透镜、候选信号、球队对阵、球员比较、相似画像、单场射门十工具调度 |
| 函数调用 | 千问 OpenAI-compatible `tool_calls`、后端参数校验与可视化执行轨迹 |
| Agent Notebook | 自动保存分析、最近记录、历史恢复、父子追问链与上下文轨迹 |
| 球探报告 | 独立报告页、指标表、证据链、来源边界及打印 / 保存 PDF |
| 千问增强 | 接入 `qwen-plus`，生成更自然的中文足球分析 |
| 安全降级 | 千问不可用时自动进入 `LOCAL SAFE MODE` |
| 前端交互 | 分析任务入口、加载状态、错误提示与重新尝试 |
| 工程能力 | 数据库迁移、统一响应结构、自动化测试与环境变量管理 |

当前数据库包含 **20 支球队、20 条最终积分榜记录、574 条球员—球队赛季记录（562 个姓名）、380 场 2024-25 完整赛果、1 场公开历史事件比赛和 28 次射门事件**，并保存本机生成的 Agent 分析快照。积分榜、赛果和球员数据使用 2024-25 口径；比赛事件是 2003/2004 独立历史快照，两个赛季不会合并计算。

新增的六赛季档案保存在 `data/processed/history/`，与原数据库统计独立。2026-10-06 导入时，每季 380 场赛程；2021-22 至 2025-26 每季均有 380 场赛果，2026-27 有 50 场赛果。当前赛季文件是抓取时的快照，实时比赛数据另由比赛中心获取。

## Agent 工作流程

```mermaid
flowchart TD
    A["自然语言问题"] --> B{"千问服务可用？"}
    B -->|是| C["Qwen tool_calls"]
    B -->|否| D["本地工具路由"]
    C --> E["后端校验并执行受控工具"]
    D --> E
    E --> F["结构化证据与数据源"]
    F --> G["千问或本地模板组织回答"]
    G --> H["答案、调用轨迹与结论边界"]
```

千问可以选择允许的工具，但不能直接访问数据库。工具名称、参数、赛季和实体均由后端校验；排名、积分、比分、xG 和球员指标仍由本地代码计算。

## 技术栈

| 层级 | 技术 |
|---|---|
| 前端 | Next.js、React、TypeScript、Tailwind CSS、React Leaflet |
| 地图 | Leaflet、OpenStreetMap 标准瓦片 |
| 后端 | Python、FastAPI、Pydantic |
| 数据层 | SQLite、SQLAlchemy、Alembic |
| 公开事件数据 | StatsBomb Open Data |
| 完整赛果数据 | OpenFootball English Results（CC0） |
| 多赛季档案 | OpenFootball JSON、固定上游提交与 SHA-256 校验 |
| 新闻与实时接口 | BBC Sport RSS、API-Football、SSE 与服务端缓存 |
| 球员赛季数据 | Kaggle Top 5 League Football Player Stats v1（CC0） |
| AI 能力 | 通义千问 OpenAI-compatible API、`qwen-plus` |
| 测试与质量 | Pytest、ESLint、Next.js Build |
| 版本管理 | Git、GitHub |
| 部署配置 | Docker Compose、Next.js standalone、Caddy HTTPS |

## 本地运行

前端需要 Node.js >=22.13。使用两个终端分别运行前后端；已有可用环境可以继续使用。

### 1. 克隆项目

```powershell
git clone https://github.com/ruiyangxie434-byte/premier-league-insight-agent.git
cd premier-league-insight-agent
```

### 2. 启动后端

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

后端启动成功后访问：

- API 地址：`http://127.0.0.1:8000`
- API 文档：`http://127.0.0.1:8000/docs`

启动会自动执行 Alembic 迁移至 `20261006_0005`，保留原数据并新增账户与登录会话表。

### 3. 启动前端

新建一个终端，在项目根目录运行：

```powershell
cd frontend
npm ci
npm run dev -- --hostname 0.0.0.0
```

浏览器访问：

```text
http://localhost:3000
```

浏览器默认请求同域 `/api`，Next.js 转发到 `http://127.0.0.1:8000`。如果沿用旧 `frontend/.env.local`，将 `NEXT_PUBLIC_API_BASE_URL` 设为空，保存并重启前端：

```dotenv
NEXT_PUBLIC_API_BASE_URL=
API_INTERNAL_URL=http://127.0.0.1:8000
```

## 多赛季历史与比赛预测

访问 `/history`，选择 2021-22 至 2026-27 的赛季，查看赛程、赛果、球队积分与跨赛季趋势。球队未参加英超的赛季不填零，进行中的赛季可用场均积分比较。

积分由赛果计算，不含扣分等行政处罚，因此可能与官方积分榜不同。未开赛比赛不填成 0:0；当前赛季档案是下载快照。

预测使用训练截止日期之前的历史主客场进失球，采用泊松模型与五场先验收缩；主队主场、客队客场各至少需要五场样本。输出胜平负概率和前三个比分，尚未回测校准，也未纳入实时伤病和阵容。

在项目根目录更新档案：

```powershell
python scripts/sync_history.py
```

更新后将对应历史 JSON 一同提交到 GitHub。

## 账户与比赛中心

访问 `/account` 可以注册、登录、刷新保持登录和退出。账户与会话持久化到 SQLite，密码使用带盐 scrypt 散列，会话通过 HttpOnly / SameSite Cookie 管理。当前没有邮箱验证、密码找回或收藏功能。

访问 `/live` 可以阅读 BBC 足球新闻，并使用实时比分、按日期查赛程、首发与替补、球队名单、转会、伤病/停赛入口。实时比赛数据需在 `backend/.env` 中配置：

```dotenv
API_FOOTBALL_KEY=你自己的数据源Key
LIVE_POLL_SECONDS=60
```

修改后重启后端。Key 仅用于服务端，不要添加 `NEXT_PUBLIC_` 前缀或提交实际密钥。无 Key、套餐无权限、请求失败或旧缓存均显示对应状态；推送仅在页面打开时生效。

缓存周期：比分默认 60 秒、每日赛程 5 分钟、首发 10 分钟、新闻 15 分钟、球队名单 6 小时、伤病 4 小时、转会 24 小时。实际更新还取决于上游；默认仅使用一个后端 worker，多副本需配置共享缓存与限流。

## 手机访问与在线部署

手机和电脑连接同一局域网，保持前后端运行，手机打开 `http://电脑局域网IP:3000`。手机需要注册登录时，把这个准确地址加入 `backend/.env` 的 `FRONTEND_ORIGINS` 并重启后端。配置和防火墙步骤见 [升级说明](docs/UPGRADE_2026_10_06.md)。

线上部署需要服务器、Docker Compose 和指向服务器的域名。根目录按 `.env.example` 创建 `.env`，填写 `PUBLIC_HOST` 和可选数据源 Key，然后在服务器执行：

```bash
docker compose up -d --build
docker compose ps
docker compose logs --tail 100 backend frontend caddy
```

Caddy 配置自动 HTTPS 和同域 API 代理，数据库保存在持久卷中。当前仅提供配置，尚未验证真实容器运行或公网部署。不要执行 `docker compose down -v`，该命令会删除数据库卷。GitHub 上传源码不会自动发布网站。

## 地图配置

地图默认使用 OpenStreetMap 标准瓦片，并在地图内显示数据署名。需要切换合规的地图瓦片服务时，可在 `frontend/.env` 中设置：

```dotenv
NEXT_PUBLIC_MAP_TILE_URL=https://tile.openstreetmap.org/{z}/{x}/{y}.png
```

球队与球场坐标始终来自后端 `/api/clubs`，前端地图没有重复硬编码业务坐标。地图侧栏支持按球队、城市或球场搜索。

## 球员数据中心

访问 `http://localhost:3000/players` 可以：

- 搜索球员、球队或国籍；
- 按球队、位置与最低出场分钟筛选，并在 50 条一页的结果中翻页；
- 按累计数据或每 90 分钟指标排序；
- 选择两名球员生成位置感知百分位雷达；
- 进入球员详情，查看累计数据、每90指标和百分位条；
- 在球员详情按 450 / 1800 / 2700 分钟门槛寻找同位置相似球员；
- 查看相似分、最接近指标和最大画像差异，并一键恢复双人雷达；
- 把所选两名球员直接带入现有 Agent 继续分析。

球员快照覆盖 2024-25 英超 20 队，共 574 条球员—球队记录；默认 450 分钟门槛下有 400 条合格记录。雷达图优先使用同位置合格记录；同位置少于 3 条时回退到全部合格记录，并显示真实比较数量。球员照片按外部照片编号按需加载，权利、身份匹配和回退说明见 [`docs/PLAYER_PORTRAITS.md`](docs/PLAYER_PORTRAITS.md)；统计口径见 [`docs/PLAYER_LAB.md`](docs/PLAYER_LAB.md)。

Similarity Scout 使用七项每90指标的同位置百分位差异，并根据前锋、中场、后卫分别设置可见权重。它排除目标球员的其他转会分段；由于当前快照缺少扑救、失球与零封字段，门将页面会明确停用推荐，而不是输出误导性相似分。算法、权重与 API 见 [`docs/SIMILARITY_SCOUT.md`](docs/SIMILARITY_SCOUT.md)。

## Squad Lens

访问 `http://localhost:3000/squad` 可以：

- 在 20 支球队之间切换，并选择全部、450、900 或 1800 分钟门槛；
- 查看门将、后卫、中场与前锋的记录数、分钟占比和进球助攻；
- 核对出场时间、进球、助攻、关键传球与防守动作领跑者；
- 查看队内出场前八记录与前五分钟负荷；
- 跳转到球员详情，并核验数据来源、许可与统计边界。

接口为 `GET /api/clubs/{slug}/squad-lens`。所有汇总均来自固定历史快照；位置分钟不代表阵型，进球与助攻汇总也不替代球队赛果统计。口径见 [`docs/SQUAD_LENS.md`](docs/SQUAD_LENS.md)。

## Club Briefing Room

访问 `http://localhost:3000/briefing` 可以：

- 选择 20 支球队与 450 / 900 / 1800 分钟统一门槛；
- 在一份情报文件中查看最终排名、主客场、末五场和最长不败；
- 查看位置分钟、队内统计领跑者与前五出场负荷；
- 同时生成后卫、中场、前锋三条位置观察队列和首位历史统计候选；
- 在当前浏览器记住常用球队，并通过打印功能保存带来源与边界的 PDF。

接口为 `GET /api/clubs/{slug}/briefing`。第九个 Copilot 工具 `build_club_briefing` 复用同一组合结果；简报不查询实时阵容、伤病、身价或转会，也不输出未来预测。组合口径见 [`docs/CLUB_BRIEFING.md`](docs/CLUB_BRIEFING.md)。

## Season Timeline Lab

访问 `http://localhost:3000/timeline` 可以：

- 用滑杆或自动播放查看第 1–38 轮的完整 20 队积分榜；
- 同时叠加最多四支球队的排名轨迹，并定位当前轮次；
- 查看每队相对上轮的升降、净胜球、积分和最近五轮拿分；
- 查看榜首更替记录，以及单队赛季最高 / 最低排名和区间停留；
- 分析最佳与最低五轮窗口、最大单轮上升和下滑；
- 通过 URL 恢复指定球队与轮次，方便演示和分享。

接口为 `GET /api/form/timeline`。第十个 Copilot 工具
`trace_season_timeline` 支持球队和第 1–38 轮参数。时间轴按原始 `matchweek`
重建，延期比赛归回原轮次，因此是历史轮次复盘，不是当时逐日实时榜或未来预测。
算法、API 与边界见 [`docs/SEASON_TIMELINE_LAB.md`](docs/SEASON_TIMELINE_LAB.md)。

## Transfer Signal

访问 `http://localhost:3000/transfer` 可以：

- 在 20 支球队、四个位置和三档分钟门槛之间切换；
- 用目标球队同位置平均百分位识别三项优先观察缺口；
- 查看外队历史统计候选、信号分和分钟样本置信度；
- 同时核对候选的正向提升与低于球队基线的权衡项；
- 在门将专属指标不足时停止排名，并明确展示数据边界。

接口为 `GET /api/clubs/{slug}/transfer-signals`。信号分只用于同一历史快照内的可解释排序，不是能力总评、成交概率或转会建议；系统不包含身价、合同、工资、伤病或实时可用性。公式与边界见 [`docs/TRANSFER_SIGNAL.md`](docs/TRANSFER_SIGNAL.md)。

## 比赛实验室

访问 `http://localhost:3000/matches` 可以：

- 打开 Arsenal 4–2 Liverpool（2004-04-09）公开历史事件快照；
- 对比双方射门、总 xG、实际进球与 `Goals - xG`；
- 按球队或进球结果筛选 28 次射门；
- 在进攻半场图上按 xG 大小查看射门位置；
- 点击射门查看球员、时间、结果、身体部位和进攻方式；
- 通过 6 个进球重建比赛时间线；
- 直接查看原始事件 JSON、开放数据许可和解释边界。

原始坐标从 StatsBomb `120 × 80` 归一化至 `0–100`。清洗脚本、公式、API 与赛季边界见 [`docs/MATCH_LAB.md`](docs/MATCH_LAB.md)。

## 赛季状态实验室

访问 `http://localhost:3000/form` 可以：

- 查看 2024-25 英超 380 场最终比分汇总与 1115 个进球；
- 选择两支球队对比第 1–38 轮累计积分走势；
- 查看 20 队最终排名、整体 / 主场 / 客场记录与末五场状态；
- 从状态表进入任意球队页，查看 38 场赛果、最长不败和最近五场；
- 核对固定数据提交、CC0 许可和历史快照边界。

赛果来自 OpenFootball 固定提交，运行时不联网更新。延期比赛在积分曲线中归回原轮次，末五场按真实开球日期排序。清洗校验、公式、API 和边界见 [`docs/SEASON_FORM_LAB.md`](docs/SEASON_FORM_LAB.md)。

## Agent Notebook 与球探报告

首页 Agent 工作台会自动保存每次完成的分析。用户可以：

- 在最近记录中重新打开任意分析；
- 继承同一组球员与赛季继续追问，并按新问题重新计算指标；
- 查看父记录、追问深度和 `run_memory` 工具轨迹；
- 打开 `/reports/{run_id}` 查看独立球探报告；
- 通过浏览器打印功能保存为 PDF，报告保留指标、证据、来源和结论边界。

分析记录目前保存在项目连接的 SQLite 数据库中。账户系统已独立接入，但现有分析记录尚未按账户绑定或隔离，也没有个人云同步功能。接口、数据模型和边界见 [`docs/AGENT_NOTEBOOK.md`](docs/AGENT_NOTEBOOK.md)。

## League Copilot

访问 `http://localhost:3000/copilot` 可以：

- 用自然语言查询 2024-25 最终积分榜；
- 查询单支球队的位置结构、队内领跑者与核心负荷；
- 查询某轮积分榜、榜首变化与单队赛季排名峰谷；
- 查询一支球队某位置的历史统计候选、提升项与权衡项；
- 调用球队对阵工具完成八维历史比较与两回合直接交锋；
- 复用既有球员每90指标与证据排序工具；
- 查询一名外场球员的同位置相似画像，并解释接近项和主要差异；
- 调用 2003-04 历史比赛射门与 xG 工具，并保持赛季隔离；
- 查看模型或本地路由选择的函数、规范化参数、调用顺序和数据源；
- 在没有千问 Key 时使用同一组真实工具完成可复现演示。

工具注册、Qwen `tool_calls`、API、降级与边界见 [`docs/LEAGUE_COPILOT.md`](docs/LEAGUE_COPILOT.md)。

## 千问配置

项目未配置千问 API Key 时仍可运行，并自动使用本地安全分析模式。

如需启用千问增强：

1. 复制 `backend/.env.example` 为 `backend/.env`。
2. 按照示例文件填写自己的千问 API Key。
3. 不要将 `.env` 或真实 API Key 上传到 GitHub。

分析结果页面会显示当前模式：

- `QWEN ENHANCED`：千问调用成功。
- `LOCAL SAFE MODE`：正在使用本地分析结果。
- `QWEN TOOL CALLING`：League Copilot 由千问选择受控函数。
- `LOCAL TOOL ROUTER`：League Copilot 由本地路由选择相同函数。

## 项目测试

后端测试：

```powershell
cd backend
python -m pytest
```

前端检查：

```powershell
cd frontend
npm run lint
npx tsc --noEmit
npm run build
```

`v0.21.0` 已完成的开发验证：

- 后端：86 项测试通过，包括 8 项历史档案、预测、账户和比赛中心新增测试
- 前端：Lint 通过
- 前端：TypeScript 通过
- 前端：Production Build 通过
- `localhost:3000` 与 `127.0.0.1:3000` 均可连接开发后端，旧单一来源 `.env` 自动兼容
- 相似球员可从详情页一键带入双人雷达，球员搜索使用 250 ms 防抖且筛选时保留当前结果
- Alembic 可从空库顺序升级至 `20261006_0005`，已有数据库升级保留原数据
- v0.11.0 数据库可无损补入 574 条球员记录，并保留既有球员 ID、完整生日与球衣号码
- 首页、Season Timeline、Club Briefing、Transfer Signal、Squad Lens、League Copilot、赛季状态、报告页、比赛中心、比赛详情、球员中心、球队详情与球员详情路由构建通过
- 头像映射脚本校验固定上游快照 SHA-256，并按球员姓名、球队和出生年份消歧；映射可重复生成
- 浏览器验证六赛季切换、跨赛季比较、预测、注册、刷新保持登录、退出和同域代理
- 浏览器验证图片全部失败占位、新旧图片接口兼容、重复点击动态标签与未配置 Key 的 SSE 状态
- 390px 手机与 768px 平板主要页面无整体横向溢出；桌面首页四卡并排
- 真实 BBC RSS 请求返回新闻；Compose YAML 的结构与持久化路径检查通过

待验证：有 API-Football Key 时的真实比分、阵容、转会与伤病联调，以及 Docker 构建、运行和公网 HTTPS。安装时检测到的依赖漏洞需要在正式部署前进一步审查和修复；本次功能验证不代表依赖安全审查已完成。

## 版本进度

- [x] `v0.1.0` 前后端项目骨架与健康检查
- [x] `v0.2.0` SQLite 数据层、关系模型与基础 API
- [x] `v0.3.0` 双球员分析 Agent MVP
- [x] `v0.4.0` 通义千问增强与本地安全降级
- [x] `v0.5.0` 英格兰交互地图与球队球场探索
- [x] `v0.6.0` 完整 20 队、可排序最终积分榜与数据来源说明
- [x] `v0.7.0` Player Lab、球员详情、每90数据榜与双人雷达图
- [x] `v0.8.0` 公开比赛数据管道、射门图、xG 对比与进球时间线
- [x] `v0.9.0` Agent 分析记录、上下文追问与可打印球探报告
- [x] `v0.10.0` 380 场完整赛果、赛季状态、积分走势与球队近期结果
- [x] `v0.11.0` 千问真实函数调用、四类受控工具、执行轨迹与本地工具路由
- [x] `v0.12.0` 2024-25 全联赛球员快照、分页、位置百分位与转会记录消歧
- [x] `v0.13.0` 同位置相似球员、位置权重、画像差异解释与本地连接可靠性
- [x] `v0.14.0` 统一数据证据 API、来源目录、覆盖统计与限制说明页面
- [x] `v0.15.0` 两队对阵 API、八维历史比较、直接交锋与非预测边界
- [x] `v0.16.0` 单队阵容结构 API、可调分钟门槛、队内领跑者与 Copilot 第七工具
- [x] `v0.17.0` 球队位置缺口、外队历史统计候选、权衡项与 Copilot 第八工具
- [x] `v0.18.0` 可打印球队情报简报、浏览器球队偏好与 Copilot 第九工具
- [x] `v0.19.0` 38 轮动态积分榜、排名轨迹、榜首更替、单队赛季故事与 Copilot 第十工具
- [x] `v0.20.0` 562 位球员身份照片、统一缺图回退、首页四类功能工作台与导航整理
- [x] `v0.21.0` 六赛季档案、球队趋势、泊松预测、注册登录、足球新闻、实时数据接口与页面内比分推送
- [x] 球员头像失败/超时回退、新旧接口兼容和首页横向对比优化
- [x] 移动端布局与 Docker Compose + Caddy 部署配置
- [ ] 配置实时数据源 Key 并完成真实数据联调
- [ ] 实际容器运行、公网部署与依赖漏洞修复

## 数据说明

当前版本的球队范围、2024-25 最终积分榜、380 场赛果和 574 条球员—球队记录均为历史快照。球员快照覆盖 562 个姓名；12 条跨队附加记录按俱乐部分别保留。Match Lab 单独使用 StatsBomb Open Data 的 2003/2004 历史比赛事件。

六赛季历史档案另有固定上游提交、来源 URL、抓取时间和原始 SHA-256；新闻与实时接口按缓存周期更新，并显示来源和更新时间。这些数据不自动并入原有 2024-25 球员统计或 Copilot 十工具。统计数据许可不涵盖球员照片，照片权利属于各自权利人。

积分榜、赛果和比赛 API 都返回来源、许可与时间边界。Copilot 只调度这些已有数据工具，不把模型表述当作新数据来源；球探报告保存的也是已计算结果快照。球场坐标遵循 OpenStreetMap 署名要求，比赛页保留 StatsBomb 署名。数据边界见 [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md)，赛季时间轴见 [`docs/SEASON_TIMELINE_LAB.md`](docs/SEASON_TIMELINE_LAB.md)，球队简报见 [`docs/CLUB_BRIEFING.md`](docs/CLUB_BRIEFING.md)，函数调用见 [`docs/LEAGUE_COPILOT.md`](docs/LEAGUE_COPILOT.md)，候选信号方法见 [`docs/TRANSFER_SIGNAL.md`](docs/TRANSFER_SIGNAL.md)，阵容口径见 [`docs/SQUAD_LENS.md`](docs/SQUAD_LENS.md)，赛果与状态见 [`docs/SEASON_FORM_LAB.md`](docs/SEASON_FORM_LAB.md)，球队对阵见 [`docs/MATCHUP_LAB.md`](docs/MATCHUP_LAB.md)，球员指标见 [`docs/PLAYER_LAB.md`](docs/PLAYER_LAB.md)，相似度方法见 [`docs/SIMILARITY_SCOUT.md`](docs/SIMILARITY_SCOUT.md)，比赛清洗和解释边界见 [`docs/MATCH_LAB.md`](docs/MATCH_LAB.md)。

## 当前边界

已实现功能仍有以下边界：

- 实时比分、赛程、阵容、转会与伤病依赖 API-Football Key、套餐权限和上游更新，尚未完成真实数据联调。
- 比分推送仅在页面打开时生效，不含后台系统通知 / Web Push。
- 预测是未校准的历史统计基线，没有准确率承诺；不包含实时阵容与伤病特征。
- 六赛季档案是公开赛果快照；计算积分不含行政扣分，原有球员统计仍固定于 2024-25。
- 账户没有邮箱验证、找回密码、个人收藏；分析记录尚未按用户绑定和隔离。
- 提供部署配置，尚无已发布的公网网址；真实容器运行与依赖漏洞修复仍需完成。
- Copilot 仅使用受控数据工具，不支持无依据的自由问答。

项目当前重点是完成一条可靠的流程：

```text
自然语言问题 → 受控工具规划 → 后端查询 / 计算 → 可验证证据 → 结论边界 → 千问或本地解释
```

## 项目定位

本项目不仅是一个英超信息展示网站，更是一项覆盖以下能力的综合实践：

- 足球数据建模与数据库设计
- 后端 API 开发
- 数据清洗与衍生指标计算
- Agent 工具链设计
- 大模型安全接入
- 前后端交互与工程测试

---

如果你对项目有建议，欢迎提交 Issue。

**Premier League Insight Agent is under active development.**
