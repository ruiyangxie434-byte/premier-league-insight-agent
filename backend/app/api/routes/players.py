from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.seed import SAMPLE_SEASON
from app.database.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.player import (
    PlayerLabData,
    PlayerLabItem,
    PlayerPosition,
    PlayerSimilarityData,
    PlayerSortKey,
    PlayerSortOrder,
)
from app.services.player_lab import (
    DEFAULT_MINIMUM_MINUTES,
    find_similar_players,
    get_player_lab_item,
    list_player_lab,
)

router = APIRouter(prefix="/players", tags=["players"])


@router.get("", response_model=ApiResponse[PlayerLabData])
def list_players(
    season: Annotated[
        str,
        Query(pattern=r"^\d{4}-\d{2}$"),
    ] = SAMPLE_SEASON,
    minimum_minutes: Annotated[
        int,
        Query(ge=0, le=4000),
    ] = DEFAULT_MINIMUM_MINUTES,
    query: Annotated[str | None, Query(max_length=80)] = None,
    position: PlayerPosition | None = None,
    club_slug: Annotated[str | None, Query(max_length=140)] = None,
    sort_by: PlayerSortKey = "goals_per90",
    order: PlayerSortOrder = "desc",
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: Session = Depends(get_db),
) -> ApiResponse[PlayerLabData]:
    data = list_player_lab(
        db,
        season=season,
        minimum_minutes=minimum_minutes,
        query=query,
        position=position,
        club_slug=club_slug,
        sort_by=sort_by,
        order=order,
        limit=limit,
        offset=offset,
    )
    return ApiResponse(message="球员数据中心获取成功", data=data)


@router.get("/{slug}", response_model=ApiResponse[PlayerLabItem])
def get_player(
    slug: str,
    season: Annotated[
        str,
        Query(pattern=r"^\d{4}-\d{2}$"),
    ] = SAMPLE_SEASON,
    db: Session = Depends(get_db),
) -> ApiResponse[PlayerLabItem]:
    player = get_player_lab_item(db, slug=slug, season=season)
    if player is None:
        raise HTTPException(status_code=404, detail="未找到该球员或赛季数据")
    return ApiResponse(message="球员详情获取成功", data=player)


@router.get(
    "/{slug}/similar",
    response_model=ApiResponse[PlayerSimilarityData],
)
def get_similar_players(
    slug: str,
    season: Annotated[
        str,
        Query(pattern=r"^\d{4}-\d{2}$"),
    ] = SAMPLE_SEASON,
    minimum_minutes: Annotated[
        int,
        Query(ge=450, le=4000),
    ] = DEFAULT_MINIMUM_MINUTES,
    limit: Annotated[int, Query(ge=1, le=10)] = 5,
    db: Session = Depends(get_db),
) -> ApiResponse[PlayerSimilarityData]:
    data = find_similar_players(
        db,
        slug=slug,
        season=season,
        minimum_minutes=minimum_minutes,
        limit=limit,
    )
    if data is None:
        raise HTTPException(status_code=404, detail="未找到该球员或赛季数据")
    return ApiResponse(message="同位置相似球员获取成功", data=data)
