from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database.seed import (
    SAMPLE_SEASON,
    SEASON_RESULTS_SOURCE_KIND,
    seed_sample_data,
)
from app.database.session import create_schema
from app.models import (
    AgentRun,
    Club,
    Match,
    MatchEvent,
    Player,
    PlayerSeasonStat,
    Standing,
)


def create_test_engine():
    return create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def test_seed_is_idempotent() -> None:
    engine = create_test_engine()
    create_schema(engine)

    with Session(engine) as session:
        assert seed_sample_data(session) is True
        assert seed_sample_data(session) is False
        assert session.scalar(select(func.count(Club.id))) == 20
        assert session.scalar(select(func.count(Standing.id))) == 20
        assert session.scalar(select(func.count(Player.id))) == 574
        assert session.scalar(select(func.count(PlayerSeasonStat.id))) == 574
        assert session.scalar(select(func.count(Match.id))) == 381
        assert session.scalar(
            select(func.count(Match.id)).where(
                Match.source_kind == SEASON_RESULTS_SOURCE_KIND
            )
        ) == 380
        assert session.scalar(select(func.count(MatchEvent.id))) == 28
        assert session.scalar(select(func.count(AgentRun.id))) == 0

    engine.dispose()


def test_seed_upgrades_existing_reference_rows() -> None:
    engine = create_test_engine()
    create_schema(engine)

    with Session(engine) as session:
        seed_sample_data(session)
        palace = session.scalar(
            select(Standing)
            .join(Standing.club)
            .where(
                Club.slug == "crystal-palace",
                Standing.season == SAMPLE_SEASON,
            )
        )
        assert palace is not None

        palace.drawn = 13
        palace.lost = 12
        palace.source_kind = "sample"
        session.commit()

        assert seed_sample_data(session) is True
        session.refresh(palace)
        assert palace.drawn == 14
        assert palace.lost == 11
        assert palace.source_kind == "historical"

    engine.dispose()
