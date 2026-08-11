from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.club import Club
    from app.models.match_event import MatchEvent
    from app.models.player_season_stat import PlayerSeasonStat


class Player(Base):
    __tablename__ = "players"
    __table_args__ = (
        UniqueConstraint("club_id", "shirt_number", name="uq_players_club_shirt"),
        Index("ix_players_club_position", "club_id", "position"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    club_id: Mapped[int] = mapped_column(
        ForeignKey("clubs.id", ondelete="CASCADE"),
        index=True,
    )
    full_name: Mapped[str] = mapped_column(String(120), index=True)
    slug: Mapped[str] = mapped_column(String(140), unique=True, index=True)
    shirt_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    position: Mapped[str] = mapped_column(String(20), index=True)
    nationality: Mapped[str] = mapped_column(String(80))
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    birth_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_kind: Mapped[str] = mapped_column(
        String(20),
        default="sample",
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    club: Mapped["Club"] = relationship(back_populates="players")
    season_stats: Mapped[list["PlayerSeasonStat"]] = relationship(
        back_populates="player",
        cascade="all, delete-orphan",
    )
    match_events: Mapped[list["MatchEvent"]] = relationship(back_populates="player")
