import json
from functools import lru_cache
from pathlib import Path


@lru_cache
def portrait_codes():
    path = Path(__file__).resolve().parents[3] / 'data/processed/player_portraits_2024_25.json'
    return json.loads(path.read_text(encoding='utf-8'))['players']


def portrait_urls(slug: str):
    code = portrait_codes().get(slug)
    if not isinstance(code, int) or code <= 0:
        return []
    return [f'https://resources.premierleague.com/premierleague/photos/players/250x250/p{code}.png',
            f'https://resources.premierleague.com/premierleague25/photos/players/110x140/{code}.png']
