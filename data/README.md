# Data directory

| 目录 | 用途 | 是否建议提交完整数据 |
| --- | --- | --- |
| `raw/` | 下载后未经修改的原始数据 | 否，仅保留小样例或下载说明 |
| `processed/` | 清洗、统一字段后的数据 | 否，仅保留必要小样例 |
| `geo/` | 英格兰边界、城市和球场坐标 | 视许可证与体积决定 |
| `sample/` | 可以公开到 GitHub 的演示数据 | 是 |

每份数据都应记录来源、获取日期、许可证或使用条件，以及它属于真实公开数据还是人工示例数据。

当前提交两份必要的处理后快照：

- `processed/statsbomb_match_3749448.json`：只保留 Match Lab 所需的 28 次射门字段，可通过 `scripts/build_match_snapshot.py` 从 StatsBomb Open Data 重建；原始 2.5 MB 事件文件不进入仓库。
- `processed/openfootball_pl_2024_25.json`：包含 Season Form Lab 所需的 380 场最终比分，可通过 `scripts/build_season_results_snapshot.py` 从固定 OpenFootball 提交重建；上游文本、提交和 CC0 许可记录在快照与文档中。
