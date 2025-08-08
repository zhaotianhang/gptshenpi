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


def test_list_forms_by_user_and_status():
    client = app.test_client()
    t_admin = token(client)
    # admin creates and submits a form
    resp = client.post('/approvals', json={'data': {'amount': 1}}, headers={'Authorization': f'Bearer {t_admin}'})
    assert resp.status_code == 201
    form1 = resp.get_json()
    resp = client.post(f"/approvals/{form1['id']}/submit", headers={'Authorization': f'Bearer {t_admin}'})
    assert resp.status_code == 200

    # normal user creates a draft form
    t_user = token(client, 'user', 'user')
    resp = client.post('/approvals', json={'data': {'amount': 2}}, headers={'Authorization': f'Bearer {t_user}'})
    assert resp.status_code == 201
    form2 = resp.get_json()

    # user should only see own form
    resp = client.get('/approvals', headers={'Authorization': f'Bearer {t_user}'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert [f['id'] for f in data] == [form2['id']]

    # admin sees both forms
    resp = client.get('/approvals', headers={'Authorization': f'Bearer {t_admin}'})
    assert resp.status_code == 200
    ids = {f['id'] for f in resp.get_json()}
    assert ids == {form1['id'], form2['id']}

    # admin can filter by status
    resp = client.get('/approvals?status=submitted', headers={'Authorization': f'Bearer {t_admin}'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert [f['id'] for f in data] == [form1['id']]


def test_workflow_execution_flow():
    client = app.test_client()
    t = token(client)
    # setup template with two approval nodes
    approval.workflow_templates.append({
        'id': 1,
        'name': 'two-step',
        'steps': [
            {'id': 'n1', 'type': 'approval', 'approvers': [1], 'next': 'n2'},
            {'id': 'n2', 'type': 'approval', 'approvers': [1]},
        ],
    })
    # create form using template
    resp = client.post(
        '/approvals',
        json={'data': {'a': 1}, 'template_id': 1},
        headers={'Authorization': f'Bearer {t}'},
    )
    assert resp.status_code == 201
    form_id = resp.get_json()['id']
    # submit form -> workflow starts
    resp = client.post(f'/approvals/{form_id}/submit', headers={'Authorization': f'Bearer {t}'})
    assert resp.status_code == 200
    # fetch form to check flow state
    resp = client.get(f'/approvals/{form_id}', headers={'Authorization': f'Bearer {t}'})
    data = resp.get_json()
    assert data['workflow']['flow'][0]['status'] == 'in_progress'
    # approve first node
    resp = client.post(
        f'/approvals/{form_id}/approve',
        json={},
        headers={'Authorization': f'Bearer {t}'},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['workflow']['flow'][0]['status'] == 'approved'
    # approve second node -> completes workflow
    resp = client.post(
        f'/approvals/{form_id}/approve',
        json={},
        headers={'Authorization': f'Bearer {t}'},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['workflow']['status'] == 'approved'


def test_actor_scope_and_resubmit():
    client = app.test_client()
    t_admin = token(client)
    # template where normal user is approver
    resp = client.post(
        '/admin/templates',
        json={'steps': [{'id': 'n1', 'type': 'approval', 'approvers': [2]}]},
        headers={'Authorization': f'Bearer {t_admin}'},
    )
    assert resp.status_code == 201
    tpl = resp.get_json()
    # admin creates form and submits
    resp = client.post(
        '/approvals',
        json={'data': {'a': 1}, 'template_id': tpl['id']},
        headers={'Authorization': f'Bearer {t_admin}'},
    )
    form_id = resp.get_json()['id']
    resp = client.post(
        f'/approvals/{form_id}/submit', headers={'Authorization': f'Bearer {t_admin}'}
    )
    assert resp.status_code == 200

    t_user = token(client, 'user', 'user')
    # user should see form in actor scope
    resp = client.get('/approvals?scope=actor', headers={'Authorization': f'Bearer {t_user}'})
    assert resp.status_code == 200
    ids = [f['id'] for f in resp.get_json()]
    assert form_id in ids

    # user rejects the form
    resp = client.post(
        f'/approvals/{form_id}/reject',
        json={'comments': 'no'},
        headers={'Authorization': f'Bearer {t_user}'},
    )
    assert resp.status_code == 200

    # admin can edit after rejection and resubmit
    resp = client.put(
        f'/approvals/{form_id}',
        json={'data': {'a': 2}},
        headers={'Authorization': f'Bearer {t_admin}'},
    )
    assert resp.status_code == 200
    resp = client.post(
        f'/approvals/{form_id}/submit', headers={'Authorization': f'Bearer {t_admin}'}
    )
    assert resp.status_code == 200
