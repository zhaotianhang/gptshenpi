import os
import pytest

from app import app, reset_data
from controllers import approval


@pytest.fixture(autouse=True)
def run_around_tests():
    reset_data()
    approval.reset_data()
    yield


def token(client, username='admin', password='admin'):
    resp = client.post('/login', json={'username': username, 'password': password})
    assert resp.status_code == 200
    return resp.get_json()['token']


def test_qr_code_and_verification_flow():
    client = app.test_client()
    t = token(client)
    resp = client.post('/approvals', json={'data': {'a': 1}}, headers={'Authorization': f'Bearer {t}'})
    assert resp.status_code == 201
    form = resp.get_json()
    assert form['qr_code_path']
    assert os.path.exists(form['qr_code_path'])
    code = form['code']

    resp = client.get(f'/verification/{code}', headers={'Authorization': f'Bearer {t}'})
    assert resp.status_code == 200
    assert resp.get_json()['id'] == form['id']

    resp = client.post(
        f'/verification/{code}',
        json={'result': 'verified', 'comments': 'ok'},
        headers={'Authorization': f'Bearer {t}'},
    )
    assert resp.status_code == 200
    record = resp.get_json()
    assert record['status'] == 'verified'
    assert record['verifier_id'] == 1
    assert record['verified_at']
    assert approval.verification_records[0]['status'] == 'verified'
