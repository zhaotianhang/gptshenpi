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


def test_create_submit_reject_flow():
    client = app.test_client()
    t = token(client)
    # create
    resp = client.post('/approvals', json={'data': {'a': 1}}, headers={'Authorization': f'Bearer {t}'})
    assert resp.status_code == 201
    form = resp.get_json()
    assert form['applicant_id'] == 1
    assert form['org_id'] == 1
    assert form['dept_id'] == 1
    assert form['code']
    form_id = form['id']
    # update
    resp = client.put(f'/approvals/{form_id}', json={'data': {'a': 2}}, headers={'Authorization': f'Bearer {t}'})
    assert resp.status_code == 200
    assert resp.get_json()['data']['a'] == 2
    # submit
    resp = client.post(f'/approvals/{form_id}/submit', headers={'Authorization': f'Bearer {t}'})
    assert resp.status_code == 200
    submitted = resp.get_json()
    assert submitted['status'] == 'submitted'
    assert submitted['submitted_at']
    assert len(approval.submission_records) == 1
    record = approval.submission_records[0]
    assert record['form_id'] == form_id
    assert record['submitter_id'] == 1
    assert record['submitted_at']
    # reject
    resp = client.post(
        f'/approvals/{form_id}/reject',
        json={'comments': 'no'},
        headers={'Authorization': f'Bearer {t}'},
    )
    assert resp.status_code == 200
    rejected = resp.get_json()
    assert rejected['status'] == 'rejected'
    assert len(approval.approval_records) == 1
    a_record = approval.approval_records[0]
    assert a_record['form_id'] == form_id
    assert a_record['approver_id'] == 1
    assert a_record['result'] == 'rejected'
    assert a_record['submission_id'] == record['id']
    assert a_record['comments'] == 'no'
    assert a_record['acted_at']


def test_create_submit_approve_flow():
    client = app.test_client()
    t = token(client)
    # create with optional verification flag
    resp = client.post(
        '/approvals',
        json={'data': {'a': 1}},
        headers={'Authorization': f'Bearer {t}'},
    )
    assert resp.status_code == 201
    form = resp.get_json()
    form_id = form['id']
    # submit
    resp = client.post(
        f'/approvals/{form_id}/submit', headers={'Authorization': f'Bearer {t}'}
    )
    assert resp.status_code == 200
    record = approval.submission_records[0]
    # approve
    resp = client.post(
        f'/approvals/{form_id}/approve',
        json={'comments': 'ok'},
        headers={'Authorization': f'Bearer {t}'},
    )
    assert resp.status_code == 200
    approved = resp.get_json()
    assert approved['status'] == 'approved'
    assert len(approval.approval_records) == 1
    a_record = approval.approval_records[0]
    assert a_record['form_id'] == form_id
    assert a_record['approver_id'] == 1
    assert a_record['result'] == 'approved'
    assert a_record['submission_id'] == record['id']
    assert a_record['comments'] == 'ok'
    assert a_record['acted_at']
    # no verification triggered by default
    assert approval.verification_records == []
