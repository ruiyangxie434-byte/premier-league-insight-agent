from datetime import date
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.database.seed import seed_sample_data
from app.models import Player, PlayerSeasonStat


def test_v011_database_upgrades_without_replacing_existing_player(
    tmp_path: Path,
    monkeypatch,
) -> None:
    database_path = tmp_path / "legacy-v011.db"
    database_url = f"sqlite:///{database_path.as_posix()}"
    backend_root = Path(__file__).resolve().parents[1]
    config = Config(str(backend_root / "alembic.ini"))
    config.set_main_option("script_location", str(backend_root / "migrations"))
    monkeypatch.setenv("DATABASE_URL", database_url)
    get_settings.cache_clear()

    try:
        command.upgrade(config, "20260808_0003")
        engine = create_engine(database_url)
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO clubs (
                        id, name, short_name, slug, city, stadium_name,
                        stadium_latitude, stadium_longitude, founded_year,
                        primary_color, source_kind
                    ) VALUES (
                        1, 'Arsenal', 'Arsenal', 'arsenal', 'London',
                        'Emirates Stadium', 51.5549, -0.1084, 1886,
                        '#ef0107', 'reference'
                    )
                    """
                )
            )
            connection.execute(
                text(
                    """
                    INSERT INTO players (
                        id, club_id, full_name, slug, shirt_number, position,
                        nationality, date_of_birth, source_kind
                    ) VALUES (
                        99, 1, 'Bukayo Saka', 'bukayo-saka', 7, 'FWD',
                        'England', '2001-09-05', 'sample'
                    )
                    """
                )
            )
            connection.execute(
                text(
                    """
                    INSERT INTO player_season_stats (
                        id, player_id, season, appearances, starts, minutes,
                        goals, assists, shots, key_passes, tackles,
                        interceptions, expected_goals, source_kind
                    ) VALUES (
                        99, 99, '2024-25', 25, 24, 2100, 6, 10, 63, 61,
                        22, 9, 8.4, 'sample'
                    )
                    """
                )
            )

        command.upgrade(config, "head")
        with Session(engine) as session:
            assert seed_sample_data(session) is True
            saka = session.scalar(
                select(Player).where(Player.slug == "bukayo-saka")
            )
            assert saka is not None
            assert saka.id == 99
            assert saka.shirt_number == 7
            assert saka.date_of_birth == date(2001, 9, 5)
            assert saka.birth_year == 2001
            assert saka.source_kind == "kaggle-fbref"
            assert session.scalar(select(func.count(Player.id))) == 574
            assert session.scalar(
                select(func.count(PlayerSeasonStat.id))
            ) == 574
            assert seed_sample_data(session) is False
        engine.dispose()
    finally:
        get_settings.cache_clear()
