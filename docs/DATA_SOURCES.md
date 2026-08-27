# 数据来源与口径

## 2024-25 最终积分榜

- 范围：2024-25 英超 20 支球队、38 轮最终排名。
- 快照日期：2025-05-25。
- 字段：排名、场次、胜、平、负、进球、失球、净胜球、积分。
- 来源：[Premier League official table](https://www.premierleague.com/en/tables/premier-league/2024-25/all-matchweeks)。
- 数据性质：静态历史快照，不是当前赛季实时积分榜。

后端会在 `/api/standings` 响应中返回来源名称、来源 URL、快照日期和是否完整，前端同时展示这些边界。

## 2024-25 完整赛果与球队状态

- 范围：2024-25 英超 38 轮、20 队、380 场最终比分，共 1115 个进球。
- 快照日期：2025-05-25。
- 来源：[OpenFootball English Results](https://github.com/openfootball/eng-england)，固定提交 `4f413c4b20129e51d43439a0f4d2c4d1b1be7482`。
- 许可：[CC0 1.0 Universal](https://github.com/openfootball/eng-england/blob/4f413c4b20129e51d43439a0f4d2c4d1b1be7482/LICENSE.md)。
- 用途：赛季总览、38 轮累计积分、主客场记录、末五场状态和球队近期赛果。
- 数据性质：已完赛历史比分快照，不是实时赛程、比赛过程数据或预测依据。

赛果以 `source_kind = openfootball` 写入现有比赛表，与 StatsBomb 单场事件的 `open-data` 标记分开。清洗校验、公式与 API 见 [`SEASON_FORM_LAB.md`](SEASON_FORM_LAB.md)。

## 球队与球场

- 球队范围与赛季保持一致，共 20 支。
- 球场名称和所在城市按 2024-25 赛季口径整理。
- 经纬度用于地图定位，是地理参考值，不用于测绘或精确导航。
- 地图瓦片和地理署名遵循 [OpenStreetMap Copyright and License](https://www.openstreetmap.org/copyright)。

## 2024-25 球员与分析指标

- 来源：[Kaggle · Top 5 League Football Player Stats (2017-2025)](https://www.kaggle.com/datasets/emrey3lmaz/top-5-league-football-player-stats-2017-2025)，固定数据集版本 v1。
- 上游更新时间：2026-04-18；上游说明为使用 `soccerdata` 从 FBref 收集。
- 许可：[CC0: Public Domain](https://creativecommons.org/publicdomain/zero/1.0/)。
- 范围：2024-25 英超 574 条球员—球队记录、562 个球员姓名、20 支球队；12 条跨队附加记录按俱乐部分别保留。
- 分析池：默认不少于 450 分钟，共 400 条记录；页面也可查看全部记录或切换 1800 / 2700 分钟门槛。
- 数据库标记：`source_kind = kaggle-fbref`。
- 数据性质：固定历史快照，不是实时名单、转会、伤病或比赛状态数据。

`scripts/build_player_snapshot.py` 固定 Kaggle v1 压缩包和 CSV 校验和，只保留姓名、球队、位置、国籍、出生年份、出场时间和本项目使用的累计表现字段。应用运行时只读取提交的紧凑 JSON，不访问 Kaggle。Similarity Scout 与 Transfer Signal 都只对同一快照的每90百分位做确定性计算，不引入新的外部数据；Club Briefing 只组合赛果、阵容与候选模块，不把组合文本当作新来源。每90分钟、百分位、分页和转会记录见 [`PLAYER_LAB.md`](PLAYER_LAB.md)，相似度权重与边界见 [`SIMILARITY_SCOUT.md`](SIMILARITY_SCOUT.md)，候选信号方法见 [`TRANSFER_SIGNAL.md`](TRANSFER_SIGNAL.md)，球队简报见 [`CLUB_BRIEFING.md`](CLUB_BRIEFING.md)。

## 历史比赛事件

- 当前比赛快照：2003/2004 Premier League，Arsenal 4–2 Liverpool，2004-04-09。
- 来源：[StatsBomb Open Data](https://github.com/hudl/open-data)，Match ID `3749448`。
- 范围：28 次 `Shot` 事件，包括时间、球员、球队、结果、位置、xG、身体部位与进攻方式。
- 坐标：从 StatsBomb `120 × 80` 线性归一化到数据库的 `0–100 × 0–100`。
- 许可：使用和再发布前阅读上游 [`LICENSE.pdf`](https://github.com/hudl/open-data/blob/master/LICENSE.pdf)，页面与 API 保留 StatsBomb 署名。
- 详细清洗步骤、公式和边界见 [`MATCH_LAB.md`](MATCH_LAB.md)。

这场历史比赛不会与 2024-25 球员快照合并计算，也不代表当前球队状态。

## Agent 分析记录与球探报告

- `agent_runs` 保存的是后端已经完成计算的分析结果快照，不是新的足球数据来源。
- 追问会继承父记录的球员与赛季范围，但会按新问题重新计算每 90 分钟指标、百分位、权重和证据排序。
- 双球员分析固定使用 2024-25 球员快照中达到 450 分钟的 400 条记录作为比较池。
- 用户问题、千问表述与本地模板结论不能作为统计事实。
- 分析记录当前只保存在项目连接的数据库中，没有用户账号、云同步或公开分享权限模型。

## League Copilot 工具边界

- Copilot 不引入新的足球数据源，只调度本页已经说明的积分榜、完整赛果、球员快照和历史比赛事件。
- `get_league_table`、`get_club_form` 与 `compare_clubs` 使用 2024-25 数据；球队对阵工具从完整赛果计算八维历史比较与两回合交锋，不输出预测。`analyze_club_squad` 使用球员—俱乐部分段汇总单队位置分钟与队内贡献，不代表阵型或实时名单。`scout_transfer_signals` 使用目标球队同位置平均百分位建立基线，只返回历史统计候选和权衡项，不读取身价、合同、工资或实时新闻。`compare_players` 使用 400 条 450+ 分钟记录；`find_similar_players` 使用同一球员快照的同位置百分位画像；`get_match_shot_summary` 只使用 2003-04 的 Match ID `3749448`。
- 同一姓名对应多个俱乐部记录时，用户必须提供俱乐部上下文；系统不会猜测要比较哪段记录。
- 千问返回的工具名称和参数必须经过后端白名单与 Pydantic 校验，模型不能直接访问数据库。
- 页面展示每次调用的规范化参数、结构化证据、来源与限制；千问或本地模板生成的文字不是新的统计事实。
- Copilot 查询当前不写入 `agent_runs`，也不会把一次问题的结果隐式带到下一次。
- 详细流程与 API 见 [`LEAGUE_COPILOT.md`](LEAGUE_COPILOT.md)。

## 更新原则

1. 历史快照保持赛季和日期不变，不静默替换为当前赛季数据。
2. 引入新赛季时使用新的赛季标识，并保留来源 URL、版本、更新时间和校验和。
3. 导入真实比赛事件或球员统计前，先记录许可、字段口径和清洗步骤。
4. 无法确认来源、许可或更新时间的数据不进入正式分析结论。
5. 外部数据只提交经过字段筛选的可复现快照，不把大体积原始文件直接纳入仓库。
