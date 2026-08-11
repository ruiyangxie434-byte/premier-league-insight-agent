# Scripts

可重复执行的数据下载、清洗与更新脚本放在这里。当前数据库初始化入口位于
`backend/app/database/init_db.py`，在 `backend/` 运行
`python -m app.database.init_db` 即可。后续外部数据脚本应从环境变量读取配置，并记录数据来源与更新时间。

## 生成 Match Lab 快照

`build_match_snapshot.py` 读取 StatsBomb Open Data 的比赛与事件 JSON，筛选 Match ID `3749448`，验证 28 次射门，归一化坐标，并生成 API 使用的紧凑快照。

```powershell
python .\scripts\build_match_snapshot.py
```

应用启动时不会下载远程事件数据。来源、许可、字段与解释边界见 [`docs/MATCH_LAB.md`](../docs/MATCH_LAB.md)。

## 生成 Season Form Lab 快照

`build_season_results_snapshot.py` 读取固定 OpenFootball 提交中的 2024-25 英超结果文本，解析 380 场比分，并验证 38 轮、20 队、每队 38 场和 1115 个进球。

```powershell
python .\scripts\build_season_results_snapshot.py
```

运行中的应用只读取 `data/processed/openfootball_pl_2024_25.json`，不会联网更新赛果。来源提交、CC0 许可、指标和边界见 [`docs/SEASON_FORM_LAB.md`](../docs/SEASON_FORM_LAB.md)。

## 生成 Player Intelligence Atlas 快照

`build_player_snapshot.py` 读取 Kaggle 数据集固定 v1 压缩包，验证 ZIP 与 CSV 的 SHA-256，筛选 2024-25 英超并生成 574 条球员—球队记录。脚本还会校验 562 个姓名、20 支球队、400 条 450+ 分钟记录和总分钟数。

```powershell
python .\scripts\build_player_snapshot.py
```

也可以传入已经下载并与固定校验和一致的压缩包：

```powershell
python .\scripts\build_player_snapshot.py `
  --input C:\data\top-5-league-player-stats-v1.zip
```

运行中的应用只读取 `data/processed/kaggle_pl_players_2024_25.json`，不会联网更新球员数据。来源、许可、字段、分页和百分位边界见 [`docs/PLAYER_LAB.md`](../docs/PLAYER_LAB.md)。
