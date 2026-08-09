# Season Form Lab：完整赛果、状态与积分轨迹

`v0.10.0` 新增 `/form` 赛季状态实验室，把 2024-25 英超完整最终比分转换为可查询、可对账的球队状态：

```text
OpenFootball 固定提交 → 可复现解析与校验 → SQLite 380 场赛果
  → FastAPI 状态聚合 → 38 轮积分走势 / 主客场 / 末五场 / 球队页
```

## 数据来源

| 字段 | 内容 |
|---|---|
| 赛事 | English Premier League |
| 赛季 | 2024-25 |
| 范围 | 38 轮、20 队、380 场最终比分 |
| 进球 | 1115 |
| 快照日期 | 2025-05-25 |
| 来源 | [OpenFootball English Results](https://github.com/openfootball/eng-england) |
| 固定提交 | `4f413c4b20129e51d43439a0f4d2c4d1b1be7482` |
| 许可 | [CC0 1.0 Universal](https://github.com/openfootball/eng-england/blob/4f413c4b20129e51d43439a0f4d2c4d1b1be7482/LICENSE.md) |

项目使用固定提交中的 `2024-25/1-premierleague.txt`，而不是跟随上游 `master` 静默更新。运行中的 API 只读取本仓库的紧凑 JSON 快照，不请求远程站点。

## 可复现快照

`scripts/build_season_results_snapshot.py` 会：

1. 识别比赛轮次、日期、开球时间、主客队和最终比分；
2. 把 20 个上游球队名称映射到项目现有球队 slug；
3. 使用 `Europe/London` 解释开球时间，并保存带时区的 ISO 时间；
4. 根据赛季、轮次和双方球队生成稳定来源 ID；
5. 验证 380 场、38 轮每轮 10 场、20 队每队 38 场；
6. 验证全赛季共 1115 个进球，进球与失球总量相等；
7. 生成 `data/processed/openfootball_pl_2024_25.json`。

从固定上游提交重建：

```powershell
python .\scripts\build_season_results_snapshot.py
```

也可以使用已经下载的原始文本：

```powershell
python .\scripts\build_season_results_snapshot.py `
  --input C:\data\1-premierleague.txt
```

## 数据库存储

赛果复用现有 `matches` 表，以 `source_kind = openfootball` 与 StatsBomb 事件比赛的 `source_kind = open-data` 分开。

- 旧数据库不需要删除，也不需要新增表；应用启动时幂等补入 380 场赛果。
- `source_match_id` 以 `of-2425-` 开头，用于稳定更新同一场比赛。
- `venue` 使用现有主队球场字段。
- SQLite 中的 `kickoff_at` 统一保存为无时区 UTC 时间，接口返回后只用于历史日期展示。
- OpenFootball 赛果不包含射门事件，因此不会进入 Match Lab 的射门或 xG 聚合。

## 指标口径

- 胜 / 平 / 负：只比较最终主客队进球。
- 积分：胜 3 分、平 1 分、负 0 分。
- 积分走势：把每支球队对应比赛轮次的积分按第 1–38 轮累加；延期比赛仍归到原轮次。
- 末五场：按真实开球日期排序后取最后 5 场，不按比赛轮次编号排序。
- 主客场拆分：分别聚合 19 个主场和 19 个客场。
- PPG：总积分除以已赛场次，保留两位小数。
- 最长不败：按真实开球日期连续统计不为负的比赛，平局会延续不败序列。

所有 20 队的胜平负、进失球和积分都会在测试中与项目的最终积分榜逐项对账。

## API

### `GET /api/form?season=2024-25`

返回：

- 380 场、1115 球、主胜 / 平局 / 客胜总量；
- 20 队最终排名、整体 / 主场 / 客场记录；
- 每队末五场状态与末五场积分；
- 每队 38 个累计积分点；
- 固定数据文件、提交和 CC0 许可地址。

### `GET /api/form/clubs/{slug}?season=2024-25`

返回单队 38 场按日期排序的赛果、对手、主客场、单场积分、赛季记录、最长不败和积分轨迹。

无效赛季格式返回统一 `422`；当前未提供的赛季或未知球队返回统一 `404`。

## 前端展示

- `/form`：赛季摘要、双队选择、38 轮积分折线、20 队状态表和数据来源。
- `/clubs/{slug}`：最终排名、赛季记录、进失球、最长不败、主客场拆分与最近五场。
- 首页提供 Season Form Lab 入口。

## 边界

- 这是 2024-25 已完赛历史快照，不是 2026-27 实时赛程或当前球队状态。
- 数据只有最终比分，不能推导 xG、控球率、射门、阵型或比赛过程。
- 末五场状态是描述性结果，不构成预测模型。
- StatsBomb 2003/2004 单场事件、2024-25 球员样例和本赛季比分属于不同数据范围，API 与页面不会混合计算。
