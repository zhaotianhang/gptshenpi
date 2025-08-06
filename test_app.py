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


def test_admin_can_manage_templates():
    client = app.test_client()
    t = token(client, 'admin', 'admin')
    resp = client.post(
        '/admin/templates',
        json={'name': 'T1', 'steps': ['a', 'b']},
        headers={'Authorization': f'Bearer {t}'},
    )
    assert resp.status_code == 201
    tpl = resp.get_json()
    tid = tpl['id']
    resp = client.put(
        f'/admin/templates/{tid}',
        json={'verifier_id': 2},
        headers={'Authorization': f'Bearer {t}'},
    )
    assert resp.status_code == 200
    assert resp.get_json()['verifier_id'] == 2
    resp = client.get('/admin/templates', headers={'Authorization': f'Bearer {t}'})
    assert resp.status_code == 200
    assert any(t['id'] == tid for t in resp.get_json())
    resp = client.delete(f'/admin/templates/{tid}', headers={'Authorization': f'Bearer {t}'})
    assert resp.status_code == 204


def test_admin_can_manage_verifiers():
    client = app.test_client()
    t = token(client, 'admin', 'admin')
    resp = client.post('/admin/verifiers', json={'user_id': 2}, headers={'Authorization': f'Bearer {t}'})
    assert resp.status_code == 201
    resp = client.get('/admin/verifiers', headers={'Authorization': f'Bearer {t}'})
    assert resp.status_code == 200
    assert 2 in resp.get_json()
    resp = client.delete('/admin/verifiers/2', headers={'Authorization': f'Bearer {t}'})
    assert resp.status_code == 204


def test_admin_can_manage_orgs_and_depts():
    client = app.test_client()
    t = token(client, 'admin', 'admin')
    resp = client.post('/admin/orgs', json={'name': 'O2'}, headers={'Authorization': f'Bearer {t}'})
    assert resp.status_code == 201
    resp = client.get('/admin/orgs', headers={'Authorization': f'Bearer {t}'})
    assert resp.status_code == 200
    assert any(o['name'] == 'O2' for o in resp.get_json())
    resp = client.post('/admin/depts', json={'name': 'D2', 'org_id': 1}, headers={'Authorization': f'Bearer {t}'})
    assert resp.status_code == 201
    resp = client.get('/admin/depts', headers={'Authorization': f'Bearer {t}'})
    assert resp.status_code == 200
    assert any(d['name'] == 'D2' for d in resp.get_json())


def test_user_cannot_create_template():
    client = app.test_client()
    t = token(client, 'user', 'user')
    resp = client.post(
        '/admin/templates',
        json={'name': 'T2', 'steps': []},
        headers={'Authorization': f'Bearer {t}'},
    )
    assert resp.status_code == 403
