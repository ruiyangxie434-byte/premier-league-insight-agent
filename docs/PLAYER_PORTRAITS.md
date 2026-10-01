# 球员定妆照

`v0.20.0` 为 2024-25 球员赛季记录增加照片。映射覆盖 574 条球员—球队记录和 562 个球员身份；同一球员在赛季内转会时仍使用同一个照片编号。球员姓名、球队、出场表现和赛季边界仍以项目的 Kaggle / FBref 历史快照为准，照片不用于推断某段记录对应的球队或球衣。

## 来源与匹配

- 照片由 Premier League 图片服务提供：`resources.premierleague.com`。应用首先请求 `/premierleague/photos/players/250x250/p{code}.png`，失败后再请求备用图片路径；图片均按需远程加载，不把照片二进制文件复制进仓库。
- 球员编号由 Fantasy Premier League 2024-25 球员资料表中的 `code` 字段提供。映射脚本固定上游提交 `59c767596750f554ba464de94cf4fce8664a6cbe` 和 SHA-256，并按姓名、球队和可用的出生年份做匹配；少数写法差异使用脚本内经过核对的别名表。
- 可复现映射：`python scripts/build_player_portraits.py <players_raw.csv>`。完整来源记录写入 `data/processed/player_portraits_2024_25.json`，浏览器只加载精简的 slug 到照片编号表 `frontend/lib/player-portrait-codes.json`。

## 显示与限制

- 名单、球员详情、球队阵容、对比和球员候选卡片统一显示对应球员照片。图片延迟加载，Next.js 图片优化会按显示尺寸传输。
- 如果主图和备用图都不可用，组件会显示球员姓名首字母，不出现破损图片图标。
- 照片服务及照片权利属于各自权利人；项目不声称拥有照片，也不把 Kaggle 数据的 CC0 许可套用到照片。上游图片可能调整、替换或下线，球衣因此可能与 2024-25 统计记录不一致。
- 比如 Neto 在 2024-25 英超出场记录对应 Bournemouth，而 FPL 照片目录所列所属队可能随租借信息变化。映射只用于辨认人物；球队统计仍按原始比赛记录分段保存。
