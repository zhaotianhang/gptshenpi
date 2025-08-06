import pytest
from app import app, reset_data
from controllers import approval


@pytest.fixture(autouse=True)
def run_around_tests():
    reset_data()
    approval.reset_data()
    yield


def token(client):
    resp = client.post('/login', json={'username': 'admin', 'password': 'admin'})
    assert resp.status_code == 200
    return resp.get_json()['token']


def test_statistics_queries_and_export():
    client = app.test_client()
    t = token(client)

    # approved form
    resp = client.post(
        '/approvals',
        json={'data': {'amount': 100}},
        headers={'Authorization': f'Bearer {t}'},
    )
    form1 = resp.get_json()
    form1_id = form1['id']
    client.post(f'/approvals/{form1_id}/submit', headers={'Authorization': f'Bearer {t}'})
    client.post(
        f'/approvals/{form1_id}/approve', json={}, headers={'Authorization': f'Bearer {t}'}
    )

    # form requiring verification
    resp = client.post(
        '/approvals',
        json={'data': {'amount': 70, 'requires_verification': True}},
        headers={'Authorization': f'Bearer {t}'},
    )
    form2 = resp.get_json()
    form2_id = form2['id']
    code2 = form2['code']
    client.post(f'/approvals/{form2_id}/submit', headers={'Authorization': f'Bearer {t}'})
    client.post(
        f'/approvals/{form2_id}/approve', json={}, headers={'Authorization': f'Bearer {t}'}
    )
    client.post(
        f'/verification/{code2}',
        json={'result': 'verified'},
        headers={'Authorization': f'Bearer {t}'},
    )

    # overall statistics
    resp = client.get('/statistics/approvals', headers={'Authorization': f'Bearer {t}'})
    assert resp.status_code == 200
    stats = resp.get_json()
    assert stats['total'] == 2
    assert stats['total_amount'] == 170

    # filter approved
    resp = client.get(
        '/statistics/approvals?status=approved',
        headers={'Authorization': f'Bearer {t}'},
    )
    stats = resp.get_json()
    assert stats['total'] == 1
    assert stats['total_amount'] == 100

    # pagination
    resp = client.get(
        '/statistics/approvals?per_page=1&page=1',
        headers={'Authorization': f'Bearer {t}'},
    )
    stats = resp.get_json()
    assert stats['total'] == 2
    assert len(stats['items']) == 1

    # export csv
    resp = client.get(
        '/statistics/approvals?status=approved&export=csv',
        headers={'Authorization': f'Bearer {t}'},
    )
    assert resp.status_code == 200
    assert resp.mimetype == 'text/csv'
    assert b'amount' in resp.data

    # verification statistics
    resp = client.get(
        '/statistics/verification?status=verified',
        headers={'Authorization': f'Bearer {t}'},
    )
    assert resp.status_code == 200
    vstats = resp.get_json()
    assert vstats['total'] == 1
    assert vstats['total_amount'] == 70
