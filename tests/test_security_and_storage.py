import json
import os
from concurrent.futures import ThreadPoolExecutor
from starlette.requests import Request
import pytest
from fastapi import HTTPException
from security import issue_session, authorized
import storage


def request(cookie='', bearer=''):
    return Request({'type': 'http', 'headers': [(b'cookie', ('autopost_session=' + cookie).encode()), (b'authorization', bearer.encode())]})


def test_session_requires_valid_signature(monkeypatch):
    monkeypatch.setenv('APP_ACCESS_TOKEN', 'fixture-access-code-with-32-characters')
    token = issue_session()
    assert authorized(request(token))
    assert not authorized(request(token + 'x'))
    assert not authorized(request())
    assert authorized(request(bearer='Bearer fixture-access-code-with-32-characters'))


def test_missing_access_configuration_denies(monkeypatch):
    monkeypatch.delenv('APP_ACCESS_TOKEN', raising=False)
    with pytest.raises(HTTPException) as error: authorized(request())
    assert error.value.status_code == 503


def test_atomic_storage_and_single_use_oauth(tmp_path, monkeypatch):
    path = tmp_path / 'db.json'
    monkeypatch.setattr(storage, 'DB_PATH', str(path))
    storage.set_oauth_state('fixture-state')
    assert storage.consume_oauth_state('wrong') is False
    assert storage.consume_oauth_state('fixture-state') is True
    assert storage.consume_oauth_state('fixture-state') is False
    assert json.loads(path.read_text())['oauth_state'] is None
    if os.name != 'nt': assert path.stat().st_mode & 0o777 == 0o600


def test_parallel_writes_do_not_lose_inputs(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, 'DB_PATH', str(tmp_path / 'db.json'))
    with ThreadPoolExecutor(max_workers=8) as pool:
        rows = list(pool.map(lambda i: storage.add_input({'text': str(i)}), range(30)))
    assert len(storage.get_pending_inputs()) == 30
    assert len({row['id'] for row in rows}) == 30
