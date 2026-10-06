"""Fetch reproducible OpenFootball seasons without changing the legacy database."""
import argparse
import hashlib
import json
import os
import ssl
import re
from datetime import datetime, timezone
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seasons', nargs='+', default=['2021-22', '2022-23', '2023-24', '2024-25', '2025-26', '2026-27'])
    parser.add_argument('--commit', help='Optional fixed upstream commit SHA')
    args = parser.parse_args()
    if args.commit and not re.fullmatch(r'[0-9a-f]{40}', args.commit):
        raise ValueError('Invalid upstream commit')
    # A fixed host, no caller-controlled URL or filesystem path.
    with httpx.Client(proxy=os.environ.get('HTTPS_PROXY'), trust_env=False, verify=ssl.create_default_context(), timeout=30) as client:
        commit = args.commit
        if not commit:
            response = client.get('https://api.github.com/repos/openfootball/football.json/commits/master')
            response.raise_for_status()
            commit = response.json()['sha']
        for season in args.seasons:
            if not re.fullmatch(r'20\d{2}-\d{2}', season):
                raise ValueError('Invalid season')
            url = f'https://raw.githubusercontent.com/openfootball/football.json/{commit}/{season}/en.1.json'
            response = client.get(url)
            response.raise_for_status()
            payload = response.json()
            matches = payload.get('matches', [])
            if not matches or not all('team1' in m and 'team2' in m and 'date' in m for m in matches):
                raise ValueError(f'{season}: invalid upstream format')
            for match in matches:
                # Upstream also uses legacy [home, away] final scores for 0-0 games.
                raw_score = match.get('score')
                if isinstance(raw_score, list) and len(raw_score) == 2 and all(isinstance(n, int) and n >= 0 for n in raw_score):
                    match['score'] = {'ft': raw_score}
                elif raw_score in ([], None):
                    match['score'] = {}
                elif not isinstance(raw_score, dict):
                    raise ValueError(f'{season}: unknown score format')
                score = match.get('score', {}).get('ft')
                if score is not None and (not isinstance(score, list) or len(score) != 2 or not all(isinstance(n, int) and n >= 0 for n in score)):
                    raise ValueError(f'{season}: invalid score')
            keys = [(m['date'], m['team1'], m['team2']) for m in matches]
            if len(keys) != len(set(keys)):
                raise ValueError(f'{season}: duplicate matches')
            payload.update(season=season, source_url=url, source_commit=commit,
                           source_sha256=hashlib.sha256(response.content).hexdigest(),
                           fetched_at=datetime.now(timezone.utc).isoformat(), license='CC0-1.0')
            folder = ROOT / 'data/processed/history'
            folder.mkdir(parents=True, exist_ok=True)
            target = folder / f'{season}.json'
            temp = target.with_suffix('.tmp')
            temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            temp.replace(target)
            print(season, len(matches), 'matches')


if __name__ == '__main__':
    main()
