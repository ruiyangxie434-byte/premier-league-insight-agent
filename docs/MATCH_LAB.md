# Match Lab 数据、指标与解释边界

`v0.8.0` 新增 `/matches` 比赛中心和 `/matches/3749448` 比赛详情页，完成以下演示路径：

```text
StatsBomb Open Data → 可复现清洗 → SQLite 事件表 → FastAPI 聚合 → 射门图 / xG / 时间线
```

## 公开比赛快照

| 字段 | 内容 |
|---|---|
| 赛事 | Premier League |
| 赛季 | 2003/2004 |
| 比赛 | Arsenal 4–2 Liverpool |
| 日期 | 2004-04-09 |
| Match ID | `3749448` |
| 射门 | Arsenal 15–13 Liverpool |
| xG | Arsenal 2.006–1.941 Liverpool |
| 来源 | [StatsBomb Open Data](https://github.com/hudl/open-data) |

原始比赛元数据位于 StatsBomb Open Data 的 `data/matches/2/44.json`，事件位于
`data/events/3749448.json`。使用或再发布数据前应同时阅读仓库中的
[`LICENSE.pdf`](https://github.com/hudl/open-data/blob/master/LICENSE.pdf)。
页面使用的 StatsBomb 标识来自同一公开仓库的 `img/SB - Icon Lockup - Colour positive.png`。

## 可复现快照

项目不在运行时请求远程数据。`scripts/build_match_snapshot.py` 会从原始 JSON 中：

1. 找到 Match ID `3749448` 的比赛元数据；
2. 只保留 `Shot` 事件；
3. 保存来源事件 ID、时间、球队、球员、结果、xG、身体部位和进攻方式；
4. 验证双方球队和射门总数；
5. 生成 `data/processed/statsbomb_match_3749448.json`。

从远程公开仓库重建：

```powershell
python .\scripts\build_match_snapshot.py
```

也可以传入已经下载的原始文件：

```powershell
python .\scripts\build_match_snapshot.py `
  --matches C:\data\44.json `
  --events C:\data\3749448.json
```

脚本会验证快照必须包含 28 次射门，避免上游文件或筛选条件变化后静默生成不一致数据。

## 坐标转换

StatsBomb 事件坐标使用 `120 × 80` 球场。数据库现有约束使用 `0–100`，因此清洗脚本按下式归一化：

```text
x_normalized = x_statsbomb / 120 × 100
y_normalized = y_statsbomb / 80 × 100
```

页面只绘制进攻半场，所有射门保持 StatsBomb 的统一进攻方向。圆点位置代表射门起点，不是球员跑动轨迹；圆点面积随 xG 增加，进球使用加号标记。

## 指标口径

- `Shots`：筛选后的 `Shot` 事件数量。
- `Goals`：`shot.outcome.name == "Goal"` 的事件数量。
- `xG`：球队全部射门 `statsbomb_xg` 的总和，展示时保留两到三位小数。
- `Finishing Δ`：实际进球数减去 xG，只描述该场终结结果相对机会质量的差值。
- `Top chance`：单次 `statsbomb_xg` 最高的射门。

xG 不等于必然进球。单场 `Goals - xG` 也不能单独证明一名球员或球队具有稳定的终结能力。

## API

### `GET /api/matches`

返回可用比赛快照、双方比分、射门与 xG 汇总、数据来源和许可地址。

### `GET /api/matches/{source_match_id}`

返回单场详情与按时间排序的射门事件。当前公开 ID 为 `3749448`。

不存在的 Match ID 返回统一 `404` 错误结构。

## 赛季边界

Match Lab 使用 2003/2004 历史比赛，因为该场有来源明确且允许公开研究使用的事件数据。项目其他模块中的完整积分榜、球队地理参考和 574 条球员—球队记录属于 2024-25 赛季。

两个数据范围不会合并计算：

- 比赛页不把 2024-25 球员赛季记录写入历史比赛阵容；
- 球员页不使用 2003/2004 单场事件推导赛季指标；
- API 和页面都返回并展示真实赛季与来源边界。

## 当前限制

- 目前只接入一场比赛，用于验证事件清洗、存储、API 与可视化链路。
- 只分析射门事件，不包含控球率、传球网络、阵型或真实跑动轨迹。
- 没有把单场数据包装成实时状态、赛季全量结论或预测结果。
