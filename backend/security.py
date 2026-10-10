"""Single-owner access gate; no LinkedIn posting happens in this module."""
import hashlib
import hmac
import os
import secrets
import time

from fastapi import HTTPException, Request


def access_key():
    key = os.getenv('APP_ACCESS_TOKEN', '')
    if len(key) < 32:
        raise HTTPException(503, 'Configure APP_ACCESS_TOKEN with at least 32 random characters')
    return key


def issue_session():
    value = f'{int(time.time()) + 3600}:{secrets.token_urlsafe(24)}'
    signature = hmac.new(access_key().encode(), value.encode(), hashlib.sha256).hexdigest()
    return value + ':' + signature


def authorized(request: Request):
    key = access_key()
    auth = request.headers.get('authorization', '')
    if auth.startswith('Bearer ') and hmac.compare_digest(auth[7:], key):
        return True
    cookie = request.cookies.get('autopost_session', '')
    try:
        value, signature = cookie.rsplit(':', 1)
        expiry = int(value.split(':', 1)[0])
        expected = hmac.new(key.encode(), value.encode(), hashlib.sha256).hexdigest()
        return expiry > time.time() and hmac.compare_digest(signature, expected)
    except (ValueError, TypeError):
        return False
