import pytest

from app import app, reset_data


@pytest.fixture(autouse=True)
def run_around_tests():
    reset_data()
    yield


def token(client, username='admin', password='admin'):
    resp = client.post('/login', json={'username': username, 'password': password})
    assert resp.status_code == 200
    return resp.get_json()['token']


def test_user_can_fetch_self():
    client = app.test_client()
    t = token(client, 'user', 'user')
    resp = client.get('/users/2', headers={'Authorization': f'Bearer {t}'})
    assert resp.status_code == 200


def test_user_cannot_fetch_others():
    client = app.test_client()
    t = token(client, 'user', 'user')
    resp = client.get('/users/1', headers={'Authorization': f'Bearer {t}'})
    assert resp.status_code == 403


def test_admin_can_create_user():
    client = app.test_client()
    t = token(client, 'admin', 'admin')
    resp = client.post(
        '/admin/users',
        json={'username': 'u2', 'password': 'p', 'role': 'user', 'org_id': 1, 'dept_id': 1},
        headers={'Authorization': f'Bearer {t}'}
    )
    assert resp.status_code == 201


def test_user_cannot_create_user():
    client = app.test_client()
    t = token(client, 'user', 'user')
    resp = client.post(
        '/admin/users',
        json={'username': 'u3', 'password': 'p'},
        headers={'Authorization': f'Bearer {t}'}
    )
    assert resp.status_code == 403
