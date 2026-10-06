"""Same-origin, HttpOnly cookie authentication; passwords never leave the server."""
import hashlib
import hmac
import secrets
import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.database.session import get_db
from app.models.account import Account, AccountSession

router = APIRouter(prefix='/auth', tags=['accounts'])
COOKIE = 'pl_session'
TTL = 7 * 86400
_attempts: dict[str, deque] = defaultdict(deque)
_lock = Lock()


class Credentials(BaseModel):
    username: str = Field(min_length=3, max_length=32, pattern=r'^[A-Za-z0-9_]+$')
    password: str = Field(min_length=10, max_length=128)


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def password_hash(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    result = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()
    return salt + ':' + result


def guard(request: Request, username: str | None = None):
    # All mutations require the configured frontend Origin (also prevents login CSRF).
    if request.headers.get('origin', '').rstrip('/') not in get_settings().cors_origins:
        raise HTTPException(403, '请求来源不受信任')
    host = request.client.host if request.client else 'unknown'
    now = time.monotonic()
    with _lock:
        for key in list(_attempts):
            if not _attempts[key] or _attempts[key][-1] < now - 60:
                del _attempts[key]
        # Proxy deployments share a backend peer address. Do not cap all users at 10/min.
        buckets = [(f'peer:{host}', 100)]
        if username:
            buckets.append((f'account:{digest(username.lower())}', 10))
        for key, limit in buckets:
            queue = _attempts[key]
            while queue and queue[0] < now - 60:
                queue.popleft()
            if len(queue) >= limit:
                raise HTTPException(429, '操作过于频繁，请一分钟后再试')
        for key, _ in buckets:
            _attempts[key].append(now)



def issue_session(db: Session, account: Account, response: Response):
    token = secrets.token_urlsafe(32)
    db.execute(delete(AccountSession).where(AccountSession.expires_at <= int(time.time())))
    db.add(AccountSession(token_hash=digest(token), account_id=account.id, expires_at=int(time.time()) + TTL))
    db.commit()
    response.set_cookie(COOKIE, token, max_age=TTL, httponly=True, samesite='lax',
                        secure=get_settings().app_env != 'development', path='/')
    response.headers['Cache-Control'] = 'no-store'
    return {'success': True, 'data': {'username': account.username}}


@router.post('/register')
def register(body: Credentials, request: Request, response: Response, db: Session = Depends(get_db)):
    guard(request, body.username)
    account = Account(username=body.username.lower(), password_hash=password_hash(body.password))
    db.add(account)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, '用户名已被使用')
    return issue_session(db, account, response)


@router.post('/login')
def login(body: Credentials, request: Request, response: Response, db: Session = Depends(get_db)):
    guard(request, body.username)
    account = db.scalar(select(Account).where(Account.username == body.username.lower()))
    stored = account.password_hash if account else password_hash('dummy-password')
    if not hmac.compare_digest(stored, password_hash(body.password, stored.split(':')[0])) or not account:
        raise HTTPException(401, '用户名或密码错误')
    return issue_session(db, account, response)


@router.get('/me')
def me(request: Request, response: Response, db: Session = Depends(get_db)):
    response.headers['Cache-Control'] = 'no-store'
    token = request.cookies.get(COOKIE)
    session = db.get(AccountSession, digest(token)) if token else None
    if not session or session.expires_at <= int(time.time()):
        raise HTTPException(401, '请先登录')
    account = db.get(Account, session.account_id)
    if not account:
        raise HTTPException(401, '账户不存在')
    return {'success': True, 'data': {'username': account.username}}


@router.post('/logout')
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    guard(request)
    token = request.cookies.get(COOKIE)
    if token:
        db.execute(delete(AccountSession).where(AccountSession.token_hash == digest(token)))
        db.commit()
    response.delete_cookie(COOKIE, path='/', httponly=True, samesite='lax', secure=get_settings().app_env != 'development')
    response.headers['Cache-Control'] = 'no-store'
    return {'success': True, 'data': None}
