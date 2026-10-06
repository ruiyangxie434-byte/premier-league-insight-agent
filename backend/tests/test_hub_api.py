import asyncio
import json
from datetime import date

import httpx
import pytest
from app.api.routes import auth
from app.services import live_provider, season_archive
from app.core.config import get_settings


@pytest.fixture(autouse=True)
def reset_auth_throttle():
    auth._attempts.clear()


def test_registration_cookie_me_logout_and_login(api_client):
    headers = {'Origin': 'http://localhost:3000'}
    body = {'username': 'Ryan_123', 'password': 'test-password-123'}
    r = api_client.post('/api/auth/register', json=body, headers=headers)
    assert r.status_code == 200
    assert 'HttpOnly' in r.headers['set-cookie'] and 'SameSite=lax' in r.headers['set-cookie']
    assert 'password' not in r.text and 'token' not in r.text
    assert api_client.get('/api/auth/me').json()['data']['username'] == 'ryan_123'
    old_token = api_client.cookies.get(auth.COOKIE)
    assert api_client.post('/api/auth/logout', headers=headers).status_code == 200
    assert api_client.get('/api/auth/me').status_code == 401
    api_client.cookies.set(auth.COOKIE, old_token)
    assert api_client.get('/api/auth/me').status_code == 401
    assert api_client.post('/api/auth/login', json=body, headers=headers).status_code == 200
    assert api_client.post('/api/auth/register', json=body, headers=headers).status_code == 409
    assert api_client.post('/api/auth/login', json={**body, 'password': 'wrong-password'}, headers=headers).status_code == 401


def test_auth_origin_validation_rate_limit_and_hash(api_client):
    body = {'username': 'account', 'password': 'test-password-123'}
    assert api_client.post('/api/auth/register', json=body).status_code == 403
    assert api_client.post('/api/auth/register', json=body, headers={'Origin': 'https://evil.example'}).status_code == 403
    assert api_client.post('/api/auth/register', json={**body, 'password':'short'}, headers={'Origin':'http://localhost:3000'}).status_code == 422
    for _ in range(10):
        assert api_client.post('/api/auth/login', json=body, headers={'Origin':'http://localhost:3000'}).status_code == 401
    assert api_client.post('/api/auth/login', json=body, headers={'Origin':'http://localhost:3000'}).status_code == 429
    one, two = auth.password_hash('test-password-123'), auth.password_hash('test-password-123')
    assert one != two and 'test-password' not in one


def test_archive_integrity_and_trend(api_client):
    catalog = api_client.get('/api/hub/seasons').json()['data']['items']
    assert len(catalog) == 6
    for info in catalog:
        data = api_client.get('/api/hub/history', params={'season':info['season']}).json()['data']
        assert len(data['matches']) == 380
        assert len(data['standings']) == 20
        assert sum(r['played'] for r in data['standings']) == info['played']*2
        assert sum(r['goals_for'] for r in data['standings']) == sum(r['goals_against'] for r in data['standings'])
    rows = api_client.get('/api/hub/trend', params={'team':'Manchester City FC'}).json()['data']['items']
    assert len(rows) == 6
    assert api_client.get('/api/hub/history',params={'season':'../../secrets'}).status_code == 422
    assert api_client.get('/api/hub/history',params={'season':'2010-11'}).status_code == 404


def test_prediction_normalization_cutoff_and_validation(api_client):
    params = {'season':'2024-25','home':'Manchester City FC','away':'Arsenal FC'}
    r = api_client.get('/api/hub/prediction', params=params)
    assert r.status_code == 200
    d = r.json()['data']
    assert abs(d['home_win']+d['draw']+d['away_win']-1) < 1e-9
    assert d['sample_matches'] == 380
    assert api_client.get('/api/hub/prediction',params={**params,'away':params['home']}).status_code == 422
    assert api_client.get('/api/hub/prediction',params={**params,'before':'2024-08-17'}).status_code == 422
    early = season_archive.prediction('2024-25',params['home'],params['away'],date(2025,1,1))
    assert early['sample_matches'] < 380
    assert api_client.get('/api/hub/prediction',params={**params,'before':'2099-01-01'}).status_code == 422


def test_additive_portrait_fields(api_client):
    d = api_client.get('/api/players/erling-haaland').json()['data']
    assert d['photo_url'] == d['photo_urls'][0]
    assert len(d['photo_urls']) == 2
    assert 'resources.premierleague.com' in d['photo_url']


def test_unconfigured_live_is_explicit_and_no_fake_data(api_client, monkeypatch):
    monkeypatch.setattr(get_settings(), 'api_football_key', None)
    data = api_client.get('/api/hub/live').json()['data']
    assert data['status'] == 'not_configured'
    assert data['items'] == [] and data['updated_at'] is None
    stream = api_client.get('/api/hub/live/stream')
    assert 'text/event-stream' in stream.headers['content-type']
    assert json.loads(stream.text.split('data: ')[1])['status'] == 'not_configured'
    assert api_client.get('/api/hub/updates?kind=lineups').status_code == 422
    assert api_client.get('/api/hub/updates?kind=squad&team=-1').status_code == 422


def test_shared_cache_coalesces_and_preserves_stale():
    async def scenario():
        live_provider._cache.clear(); live_provider._locks.clear()
        calls = 0
        async def fetch():
            nonlocal calls
            calls += 1
            await asyncio.sleep(.01)
            return [{'id':1}]
        key = ('test',)
        results = await asyncio.gather(*(live_provider.cached(key,60,fetch,'test') for _ in range(10)))
        assert calls == 1 and all(r['status']=='ok' for r in results)
        original = results[0]['updated_at']
        live_provider._cache[key]['retry_at'] = 0
        async def fail():
            raise httpx.ConnectError('unavailable')
        stale = await live_provider.cached(key,60,fail,'test')
        assert stale['status'] == 'stale' and stale['updated_at'] == original and stale['items'] == [{'id':1}]
        empty = await live_provider.cached(('empty',),60,fail,'test')
        assert empty['status']=='unavailable' and empty['items']==[]
    asyncio.run(scenario())


def test_provider_errors_and_secret_not_exposed(api_client, monkeypatch):
    monkeypatch.setattr(get_settings(), 'api_football_key', 'private-test-key')
    live_provider._cache.clear(); live_provider._locks.clear()
    class FakeClient:
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def get(self, *args, **kwargs):
            return httpx.Response(200, json={'errors': {'token':'private-test-key'},'response':[]}, request=httpx.Request('GET','https://example.test'))
    monkeypatch.setattr(live_provider, 'client', FakeClient)
    r = api_client.get('/api/hub/live')
    assert r.json()['data']['status']=='unavailable'
    assert 'private-test-key' not in r.text
