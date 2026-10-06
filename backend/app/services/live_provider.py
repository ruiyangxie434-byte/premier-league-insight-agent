"""Bounded shared caches, stale-data disclosure and fixed upstream hosts."""
import asyncio
import os
import ssl
import time
from datetime import datetime, timezone
from xml.etree import ElementTree
from urllib.parse import urlparse

import httpx
from app.core.config import get_settings

_cache = {}
_locks = {}
API = 'https://v3.football.api-sports.io'
NEWS = 'https://feeds.bbci.co.uk/sport/football/rss.xml'


def stamp():
    return datetime.now(timezone.utc).isoformat()


async def cached(key, ttl, fetcher, source):
    now = time.monotonic()
    entry = _cache.get(key)
    if entry and entry['retry_at'] > now:
        return entry['value']
    # Lock entries are bounded along with the cache. Server runs one worker.
    if key not in _locks:
        if len(_cache) >= 256:
            for old in list(_cache):
                if not _locks[old].locked():
                    _cache.pop(old)
                    _locks.pop(old)
                    break
        _locks[key] = asyncio.Lock()
    async with _locks[key]:
        now = time.monotonic()
        entry = _cache.get(key)
        if entry and entry['retry_at'] > now:
            return entry['value']
        try:
            items = await fetcher()
            value = {'status': 'ok', 'items': items, 'updated_at': stamp(), 'source': source, 'message': None}
            retry = ttl
        except (httpx.HTTPError, ValueError, KeyError, TypeError, ElementTree.ParseError):
            previous = entry['value'] if entry else None
            has_previous = previous and previous['updated_at']
            value = {'status': 'stale' if has_previous else 'unavailable',
                     'items': previous['items'] if has_previous else [],
                     'updated_at': previous['updated_at'] if has_previous else None,
                     'source': source, 'message': '数据源暂不可用或当前套餐无权限，请稍后重试。旧数据已标注更新时间。'}
            retry = max(60, min(ttl, 300))
        _cache[key] = {'value': value, 'retry_at': time.monotonic()+retry}
        return value


def client():
    return httpx.AsyncClient(proxy=os.environ.get('HTTPS_PROXY'), trust_env=False,
                             verify=ssl.create_default_context(), timeout=12, follow_redirects=False)


async def football(endpoint, params, ttl):
    settings = get_settings()
    if not settings.api_football_key:
        return {'status': 'not_configured', 'items': [], 'updated_at': None, 'source': 'API-Football',
                'message': '尚未接入实时数据源。管理员配置 API_FOOTBALL_KEY 后可使用；权限与覆盖范围取决于套餐。'}

    async def fetcher():
        async with client() as session:
            response = await session.get(API+'/'+endpoint, params=params, headers={'x-apisports-key': settings.api_football_key})
            response.raise_for_status()
            data = response.json()
            if data.get('errors') or not isinstance(data.get('response'), list):
                raise ValueError('Provider error')
            # Never expose the request headers, token or upstream error body.
            return data['response']
    key = (endpoint, tuple(sorted(params.items())))
    return await cached(key, ttl, fetcher, 'API-Football')


async def news():
    async def fetcher():
        async with client() as session:
            response = await session.get(NEWS)
            response.raise_for_status()
            if len(response.content) > 2_000_000 or b'<!DOCTYPE' in response.content.upper() or b'<!ENTITY' in response.content.upper():
                raise ValueError('Invalid feed')
            root = ElementTree.fromstring(response.content)
            items = []
            for node in root.findall('./channel/item')[:20]:
                link = node.findtext('link', '')
                parsed = urlparse(link)
                if parsed.scheme != 'https' or parsed.hostname not in ('www.bbc.co.uk', 'www.bbc.com', 'bbc.co.uk', 'bbc.com'):
                    continue
                items.append({'title': node.findtext('title', '')[:300], 'url': link,
                              'published_at': node.findtext('pubDate', ''), 'source': 'BBC Sport'})
            return items
    return await cached(('news',), 900, fetcher, 'BBC Sport Football RSS')
