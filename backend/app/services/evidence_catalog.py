from app.schemas.evidence import EvidenceCatalogData, EvidenceSource


SOURCES = [
    EvidenceSource(
        id="premier-league-table",
        name="2024-25 最终积分榜",
        provider="Premier League",
        source_url="https://www.premierleague.com/en/tables/premier-league/2024-25/all-matchweeks",
        license="公开页面人工核验快照",
        coverage="2024-25 · 20 支球队",
        snapshot_date="2025-05-25",
        record_count=20,
        record_label="球队排名记录",
        powers=["积分榜", "球队赛季总结", "Copilot 联赛排名查询"],
        limitations=["历史快照，不代表当前赛季", "不提供逐场事件或预测"],
        status="ready",
    ),
    EvidenceSource(
        id="openfootball-results",
        name="2024-25 完整赛果",
        provider="OpenFootball",
        source_url="https://github.com/openfootball/eng-england",
        license="CC0 1.0",
        coverage="2024-25 · 38 轮",
        snapshot_date="2025-05-25",
        record_count=380,
        record_label="场比赛",
        powers=["赛季状态实验室", "主客场拆分", "38 轮积分走势"],
        limitations=["只包含赛果，不包含 xG 和事件坐标", "不用于未来赛果预测"],
        status="ready",
    ),
    EvidenceSource(
        id="kaggle-fbref-players",
        name="球员赛季表现快照",
        provider="Kaggle / FBref derived dataset",
        source_url="https://www.kaggle.com/datasets/emrey3lmaz/top-5-league-football-player-stats-2017-2025",
        license="CC0: Public Domain · dataset v1",
        coverage="2024-25 · 574 条球员—球队记录",
        snapshot_date="2026-04-18",
        record_count=574,
        record_label="球员—球队赛季记录",
        powers=["球员实验室", "百分位雷达", "Similarity Scout", "分析 Agent"],
        limitations=["转会球员可能有多条俱乐部分段", "门将缺少专属扑救指标", "相似度不是身价或转会建议"],
        status="limited",
    ),
    EvidenceSource(
        id="statsbomb-open-data",
        name="公开比赛事件样例",
        provider="StatsBomb Open Data",
        source_url="https://github.com/hudl/open-data",
        license="StatsBomb Open Data user agreement",
        coverage="Arsenal 4–2 Liverpool · 2003-04",
        snapshot_date="2026-07-01",
        record_count=28,
        record_label="次射门事件",
        powers=["比赛实验室", "射门图", "xG 汇总", "Copilot 单场查询"],
        limitations=["仅一场历史公开样例", "射门坐标不是球员跑动热区", "不可与 2024-25 球员快照混为同赛季证据"],
        status="limited",
    ),
]


def get_evidence_catalog() -> EvidenceCatalogData:
    return EvidenceCatalogData(
        generated_at="2026-08-14",
        season_focus="2024-25",
        sources=SOURCES,
        source_count=len(SOURCES),
        ready_count=sum(source.status == "ready" for source in SOURCES),
        total_records=sum(source.record_count for source in SOURCES),
        methodology=[
            "运行时优先查询本地结构化快照，不让模型猜测可计算结论。",
            "不同赛季与不同粒度的数据保持隔离，回答中明确标注适用范围。",
            "每90、百分位、相似度和积分走势均由后端确定性计算。",
            "数据不足时返回限制说明，不用零值或生成内容填补缺口。",
        ],
    )
