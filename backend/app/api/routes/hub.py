import asyncio
import json
from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from app.core.config import get_settings
from app.services import live_provider, season_archive

router = APIRouter(prefix='/hub', tags=['season archive and live centre'])
Season = Annotated[str, Query(pattern=r'^20\d{2}-\d{2}$')]
PositiveId = Annotated[int, Query(gt=0, le=2147483647)]
Year = Annotated[int, Query(ge=2010, le=2100)]


def result(data):
    return {'success': True, 'data': data}


@router.get('/seasons')
def seasons():
    return result({'items': season_archive.catalog()})


@router.get('/history')
def history(season: Season = '2024-25', team: Annotated[str | None, Query(max_length=120)] = None):
    return result(season_archive.archive(season, team))


@router.get('/trend')
def trend(team: Annotated[str, Query(min_length=1, max_length=120)]):
    rows = []
    for item in reversed(season_archive.catalog()):
        payload = season_archive.load(item['season'])
        row = next((row for row in season_archive.table(payload) if season_archive.team_key(row['team']) == season_archive.team_key(team)), None)
        # A missing season is absent, never represented as a zero-point relegation.
        if row:
            rows.append({'season': item['season'], **row})
    return result({'items': rows, 'notice': '仅展示档案中该队参加英超的赛季；当前赛季可能尚未结束。'})


@router.get('/prediction')
def prediction(home: Annotated[str, Query(min_length=1, max_length=120)],
               away: Annotated[str, Query(min_length=1, max_length=120)],
               season: Season = '2024-25', before: date | None = None):
    cutoff = before or date.today()
    if cutoff > date.today():
        raise HTTPException(422, '训练截止日期不能晚于今天')
    return result(season_archive.prediction(season, home, away, cutoff))


@router.get('/news')
async def news():
    return result(await live_provider.news())


@router.get('/teams')
async def teams(season: Year = 2026):
    return result(await live_provider.football('teams', {'league': 39, 'season': season}, 86400))


@router.get('/fixtures')
async def fixtures(day: date, season: Year = 2026):
    return result(await live_provider.football('fixtures', {'league': 39, 'season': season, 'date': day.isoformat(), 'timezone': 'UTC'}, 300))


@router.get('/live')
async def live():
    return result(await live_provider.football('fixtures', {'live': '39'}, max(30, get_settings().live_poll_seconds)))


@router.get('/updates')
async def updates(kind: Literal['squad', 'transfers', 'injuries', 'lineups'],
                  team: PositiveId | None = None, fixture: PositiveId | None = None, season: Year = 2026):
    if kind == 'lineups':
        if fixture is None:
            raise HTTPException(422, '请选择比赛')
        data = await live_provider.football('fixtures/lineups', {'fixture': fixture}, 600)
    else:
        if team is None:
            raise HTTPException(422, '请选择球队')
        endpoint = {'squad': 'players/squads', 'transfers': 'transfers', 'injuries': 'injuries'}[kind]
        params = {'team': team}
        if kind == 'injuries':
            params['season'] = season
        ttl = {'squad': 21600, 'transfers': 86400, 'injuries': 14400}[kind]
        data = await live_provider.football(endpoint, params, ttl)
    return result(data)


@router.get('/live/stream')
async def stream(request: Request):
    async def events():
        while not await request.is_disconnected():
            data = await live_provider.football('fixtures', {'live': '39'}, max(30, get_settings().live_poll_seconds))
            yield 'data: '+json.dumps(data, ensure_ascii=False)+'\n\n'
            if data['status'] == 'not_configured':
                break
            # Shared cache coalesces subscribers; this is in-page SSE, not background Web Push.
            for _ in range(max(30, get_settings().live_poll_seconds)):
                if await request.is_disconnected():
                    return
                await asyncio.sleep(1)
    return StreamingResponse(events(), media_type='text/event-stream',
                             headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})
