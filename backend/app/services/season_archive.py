"""An isolated archive preserves the existing 2024-25 player/API semantics."""
import json
import math
import re
from datetime import date
from pathlib import Path
from fastapi import HTTPException

FOLDER = Path(__file__).resolve().parents[3] / 'data/processed/history'


def team_key(name: str):
    cleaned = re.sub(r"\b(?:FC|AFC)\b", "", name, flags=re.I).strip().casefold()
    return {"wolves": "wolverhampton wanderers"}.get(cleaned, cleaned)


def catalog():
    items = []
    for path in sorted(FOLDER.glob('*.json'), reverse=True):
        payload = json.loads(path.read_text(encoding='utf-8'))
        matches = payload['matches']
        played = sum(len(m.get('score', {}).get('ft', [])) == 2 for m in matches)
        items.append({'season': payload['season'], 'matches': len(matches), 'played': played,
                      'fetched_at': payload['fetched_at'], 'source_url': payload['source_url']})
    return items


def load(season: str):
    if season not in {item['season'] for item in catalog()}:
        raise HTTPException(404, '该赛季尚未导入，请运行 sync_history.py')
    return json.loads((FOLDER / f'{season}.json').read_text(encoding='utf-8'))


def completed(payload, before: date | None = None):
    return [m for m in payload['matches'] if len(m.get('score', {}).get('ft', [])) == 2
            and (before is None or date.fromisoformat(m['date']) < before)]


def table(payload):
    rows = {}
    for m in payload['matches']:
        for name in (m['team1'], m['team2']):
            rows.setdefault(name, dict(team=name, played=0, won=0, drawn=0, lost=0, goals_for=0, goals_against=0, points=0))
    for m in completed(payload):
        a, b = m['score']['ft']
        for name, gf, ga in ((m['team1'], a, b), (m['team2'], b, a)):
            row = rows[name]
            row['played'] += 1
            row['won'] += gf > ga
            row['drawn'] += gf == ga
            row['lost'] += gf < ga
            row['goals_for'] += gf
            row['goals_against'] += ga
            row['points'] += 3 if gf > ga else 1 if gf == ga else 0
    ordered = sorted(rows.values(), key=lambda r: (-r['points'], -(r['goals_for']-r['goals_against']), -r['goals_for'], r['team']))
    for rank, row in enumerate(ordered, 1):
        row.update(rank=rank, goal_difference=row['goals_for']-row['goals_against'])
    return ordered


def archive(season: str, team: str | None):
    payload = load(season)
    matches = [m for m in payload['matches'] if not team or team in (m['team1'], m['team2'])]
    return {'season': season, 'standings': table(payload), 'matches': matches,
            'source_url': payload['source_url'], 'fetched_at': payload['fetched_at'],
            'notice': '积分由已录入赛果计算，不含行政扣分；排名按积分、净胜球、进球排序。日期来自公开档案，未标注时区的开球时间不作实时解读。'}


def prediction(season: str, home: str, away: str, before: date):
    if home == away:
        raise HTTPException(422, '主客队不能相同')
    payload = load(season)
    matches = completed(payload, before)
    home_games = [m for m in matches if m['team1'] == home]
    away_games = [m for m in matches if m['team2'] == away]
    if len(home_games) < 5 or len(away_games) < 5:
        raise HTTPException(422, '截止日前主客场样本各需至少 5 场，请选择更早的完整赛季')
    league_home = sum(m['score']['ft'][0] for m in matches)/len(matches)
    league_away = sum(m['score']['ft'][1] for m in matches)/len(matches)
    # Five-match shrinkage toward the league mean reduces small-sample extremes.
    home_attack = (sum(m['score']['ft'][0] for m in home_games)+5*league_home)/(len(home_games)+5)
    home_defence = (sum(m['score']['ft'][1] for m in home_games)+5*league_away)/(len(home_games)+5)
    away_attack = (sum(m['score']['ft'][1] for m in away_games)+5*league_away)/(len(away_games)+5)
    away_defence = (sum(m['score']['ft'][0] for m in away_games)+5*league_home)/(len(away_games)+5)
    lh = min(6, max(.05, home_attack*away_defence/max(.05, league_home)))
    la = min(6, max(.05, away_attack*home_defence/max(.05, league_away)))
    cells = [(h, a, math.exp(-lh-la)*lh**h/math.factorial(h)*la**a/math.factorial(a)) for h in range(21) for a in range(21)]
    mass = sum(p for _, _, p in cells)
    win = sum(p for h, a, p in cells if h > a)/mass
    draw = sum(p for h, a, p in cells if h == a)/mass
    top = sorted(cells, key=lambda c: -c[2])[:3]
    return {'home': home, 'away': away, 'season': season, 'before': before.isoformat(),
            'sample_matches': len(matches), 'home_samples': len(home_games), 'away_samples': len(away_games),
            'home_expected_goals': round(lh, 2), 'away_expected_goals': round(la, 2),
            'home_win': win, 'draw': draw, 'away_win': 1-win-draw,
            'scorelines': [{'score': f'{h}–{a}', 'probability': p/mass} for h,a,p in top],
            'source_url': payload['source_url'],
            'notice': '泊松统计基线，使用截止日前的历史主客场进失球；尚未回测或校准，不包含实时阵容、伤病、赔率，不承诺预测准确率。'}
