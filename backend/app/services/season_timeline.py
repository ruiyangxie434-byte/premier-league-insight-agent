from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database.seed import (
    SAMPLE_SEASON,
    SEASON_RESULTS_SOURCE_KIND,
    load_season_results_snapshot,
)
from app.models import Club, Match, Standing
from app.schemas.form import (
    SeasonTimelineData,
    TimelineClubStory,
    TimelineFormWindowData,
    TimelineLeaderChangeData,
    TimelineMovementData,
    TimelineRoundSnapshot,
    TimelineTableRow,
)
from app.services.season_form import form_club


TIMELINE_SNAPSHOT = load_season_results_snapshot()
TIMELINE_NOTICE = (
    "这是按原始 matchweek 重建的 2024-25 历史轮次榜，不是当时每个自然日的"
    "实时积分榜；延期比赛仍归回原比赛轮次，也不用于预测未来排名。"
)
TIMELINE_METHOD = (
    "每轮结束后按积分、净胜球、进球数和球队名做确定性排序；前三项对应"
    "常规积分榜排序，球队名只在仍完全相同时用于稳定展示。滚动状态使用"
    "最近五个比赛轮次的积分。最终轮会与项目内官方最终积分榜逐队对账。"
)


class SeasonTimelineUnavailable(RuntimeError):
    """Raised when the fixed season snapshots cannot be reconciled."""


@dataclass
class MutableRecord:
    played: int = 0
    won: int = 0
    drawn: int = 0
    lost: int = 0
    goals_for: int = 0
    goals_against: int = 0
    points: int = 0

    @property
    def goal_difference(self) -> int:
        return self.goals_for - self.goals_against


def _zone(position: int) -> str:
    if position == 1:
        return "leader"
    if position <= 4:
        return "top_four"
    if position >= 18:
        return "relegation"
    return "mid_table"


def _apply_result(record: MutableRecord, scored: int, conceded: int) -> None:
    record.played += 1
    record.goals_for += scored
    record.goals_against += conceded
    if scored > conceded:
        record.won += 1
        record.points += 3
    elif scored == conceded:
        record.drawn += 1
        record.points += 1
    else:
        record.lost += 1


def _window(
    rows: list[TimelineTableRow],
    *,
    best: bool,
) -> TimelineFormWindowData:
    eligible = [row for row in rows if row.played >= 5]
    if len(eligible) != 34:
        raise SeasonTimelineUnavailable("五场滚动窗口无法完整重建")
    chosen = (
        max(eligible, key=lambda row: (row.rolling_points, -row.matchweek))
        if best
        else min(eligible, key=lambda row: (row.rolling_points, row.matchweek))
    )
    return TimelineFormWindowData(
        start_matchweek=chosen.matchweek - 4,
        end_matchweek=chosen.matchweek,
        points=chosen.rolling_points,
        points_per_game=chosen.rolling_points_per_game,
    )


def get_season_timeline(
    db: Session,
    *,
    season: str = SAMPLE_SEASON,
) -> SeasonTimelineData:
    matches = list(
        db.scalars(
            select(Match)
            .options(
                selectinload(Match.home_club),
                selectinload(Match.away_club),
            )
            .where(
                Match.season == season,
                Match.source_kind == SEASON_RESULTS_SOURCE_KIND,
            )
            .order_by(Match.matchweek, Match.id)
        ).all()
    )
    clubs = list(db.scalars(select(Club).order_by(Club.name)).all())
    standings = list(
        db.scalars(
            select(Standing)
            .options(selectinload(Standing.club))
            .where(Standing.season == season)
            .order_by(Standing.position)
        ).all()
    )
    if len(matches) != 380 or len(clubs) != 20 or len(standings) != 20:
        raise SeasonTimelineUnavailable("赛季时间轴所需的 380 场赛果或积分榜尚未完整初始化")

    clubs_by_id = {club.id: club for club in clubs}
    records = {club.id: MutableRecord() for club in clubs}
    point_history = {club.id: [0] for club in clubs}
    previous_positions: dict[int, int] = {}
    previous_leader_id: int | None = None
    rounds: list[TimelineRoundSnapshot] = []
    leader_changes: list[TimelineLeaderChangeData] = []
    rows_by_club: dict[int, list[TimelineTableRow]] = {
        club.id: [] for club in clubs
    }

    for matchweek in range(1, 39):
        week_matches = [match for match in matches if match.matchweek == matchweek]
        if len(week_matches) != 10:
            raise SeasonTimelineUnavailable(
                f"第 {matchweek} 轮不是完整的 10 场赛果"
            )
        for match in week_matches:
            if match.home_score is None or match.away_score is None:
                raise SeasonTimelineUnavailable("赛季时间轴包含缺失比分")
            _apply_result(
                records[match.home_club_id],
                match.home_score,
                match.away_score,
            )
            _apply_result(
                records[match.away_club_id],
                match.away_score,
                match.home_score,
            )

        ranked_ids = sorted(
            records,
            key=lambda club_id: (
                -records[club_id].points,
                -records[club_id].goal_difference,
                -records[club_id].goals_for,
                clubs_by_id[club_id].name,
            ),
        )
        week_rows: list[TimelineTableRow] = []
        for position, club_id in enumerate(ranked_ids, start=1):
            record = records[club_id]
            point_history[club_id].append(record.points)
            window_size = min(5, matchweek)
            baseline_index = max(0, matchweek - window_size)
            rolling_points = record.points - point_history[club_id][baseline_index]
            previous_position = previous_positions.get(club_id)
            row = TimelineTableRow(
                matchweek=matchweek,
                position=position,
                previous_position=previous_position,
                position_change=(
                    previous_position - position
                    if previous_position is not None
                    else 0
                ),
                club=form_club(clubs_by_id[club_id]),
                played=record.played,
                won=record.won,
                drawn=record.drawn,
                lost=record.lost,
                goals_for=record.goals_for,
                goals_against=record.goals_against,
                goal_difference=record.goal_difference,
                points=record.points,
                rolling_points=rolling_points,
                rolling_points_per_game=round(rolling_points / window_size, 2),
                zone=_zone(position),
            )
            week_rows.append(row)
            rows_by_club[club_id].append(row)

        leader_id = ranked_ids[0]
        leader_changed = leader_id != previous_leader_id
        if leader_changed:
            leader_changes.append(
                TimelineLeaderChangeData(
                    matchweek=matchweek,
                    previous_leader=(
                        form_club(clubs_by_id[previous_leader_id])
                        if previous_leader_id is not None
                        else None
                    ),
                    leader=form_club(clubs_by_id[leader_id]),
                )
            )
        rounds.append(
            TimelineRoundSnapshot(
                matchweek=matchweek,
                leader=form_club(clubs_by_id[leader_id]),
                leader_changed=leader_changed,
                rows=week_rows,
            )
        )
        previous_positions = {
            row.club.id: row.position for row in week_rows
        }
        previous_leader_id = leader_id

    official_by_id = {standing.club_id: standing for standing in standings}
    final_rows = {row.club.id: row for row in rounds[-1].rows}
    for club_id, official in official_by_id.items():
        rebuilt = final_rows[club_id]
        if (
            rebuilt.position != official.position
            or rebuilt.points != official.points
            or rebuilt.goals_for != official.goals_for
            or rebuilt.goals_against != official.goals_against
        ):
            raise SeasonTimelineUnavailable(
                f"{official.club.short_name} 的最终轮重建结果未通过积分榜对账"
            )

    club_stories: list[TimelineClubStory] = []
    for standing in standings:
        club_rows = rows_by_club[standing.club_id]
        positions = [row.position for row in club_rows]
        rises = [row for row in club_rows if row.position_change > 0]
        drops = [row for row in club_rows if row.position_change < 0]
        biggest_rise_row = max(
            rises,
            key=lambda row: (row.position_change, -row.matchweek),
            default=None,
        )
        biggest_drop_row = min(
            drops,
            key=lambda row: (row.position_change, row.matchweek),
            default=None,
        )
        peak_position = min(positions)
        lowest_position = max(positions)
        club_stories.append(
            TimelineClubStory(
                club=form_club(standing.club),
                round_one_position=positions[0],
                final_position=standing.position,
                finish_change=positions[0] - standing.position,
                peak_position=peak_position,
                peak_rounds=[
                    row.matchweek
                    for row in club_rows
                    if row.position == peak_position
                ],
                lowest_position=lowest_position,
                lowest_rounds=[
                    row.matchweek
                    for row in club_rows
                    if row.position == lowest_position
                ],
                leader_rounds=sum(row.position == 1 for row in club_rows),
                top_four_rounds=sum(row.position <= 4 for row in club_rows),
                relegation_rounds=sum(row.position >= 18 for row in club_rows),
                biggest_rise=(
                    TimelineMovementData(
                        matchweek=biggest_rise_row.matchweek,
                        places=biggest_rise_row.position_change,
                    )
                    if biggest_rise_row is not None
                    else None
                ),
                biggest_drop=(
                    TimelineMovementData(
                        matchweek=biggest_drop_row.matchweek,
                        places=abs(biggest_drop_row.position_change),
                    )
                    if biggest_drop_row is not None
                    else None
                ),
                best_five_match_window=_window(club_rows, best=True),
                worst_five_match_window=_window(club_rows, best=False),
            )
        )

    source = TIMELINE_SNAPSHOT["source"]
    return SeasonTimelineData(
        competition=TIMELINE_SNAPSHOT["competition"],
        season=season,
        snapshot_date=TIMELINE_SNAPSHOT["snapshot_date"],
        total_matchweeks=38,
        match_count=len(matches),
        rounds=rounds,
        club_stories=club_stories,
        leader_changes=leader_changes,
        source_name=source["name"],
        source_url=source["data_url"],
        license_name=source["license_name"],
        license_url=source["license_url"],
        source_commit=source["source_commit"],
        sample_notice=TIMELINE_NOTICE,
        method_notice=TIMELINE_METHOD,
    )
