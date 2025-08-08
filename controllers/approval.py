from datetime import datetime
import os

try:
    import qrcode
except Exception:  # pragma: no cover - fallback if qrcode isn't installed
    qrcode = None

from flask import Blueprint, jsonify, request

from middleware.auth import authenticate_token
import storage

bp = Blueprint('approval', __name__, url_prefix='/approvals')

data = storage.data()


def _refresh_refs():
    global approval_forms, submission_records, approval_records, verification_records
    approval_forms = data.setdefault('approval_forms', [])
    submission_records = data.setdefault('submission_records', [])
    approval_records = data.setdefault('approval_records', [])
    verification_records = data.setdefault('verification_records', [])


def reset_data():
    data['approval_forms'] = []
    data['submission_records'] = []
    data['approval_records'] = []
    data['verification_records'] = []
    data['next_id'] = 1
    data['next_code'] = 1
    _refresh_refs()
    storage.save()


_refresh_refs()


def _find_form(form_id):
    return next((f for f in approval_forms if f['id'] == form_id), None)


def _find_submission_record(form_id):
    return next((r for r in submission_records if r['form_id'] == form_id), None)


def _find_template(template_id):
    return next((t for t in workflow_templates if t['id'] == template_id), None)


def _after_approval(form, result):
    """Trigger verification or finalize the workflow after approval."""
    if result == 'approved':
        if form['data'].get('requires_verification'):
            vr = {
                'id': len(verification_records) + 1,
                'form_id': form['id'],
                'status': 'pending',
                'verifier_id': None,
                'verified_at': None,
                'comments': None,
            }
            verification_records.append(vr)
            form['status'] = 'verification_pending'
        else:
            form['status'] = 'approved'
    else:
        form['status'] = 'rejected'
    storage.save()


@bp.get('')
@authenticate_token
def list_forms():
    """Return approval forms visible to the current user.

    Regular users can request either forms they created or forms they
    need to act on via the ``scope`` query parameter. Admins may view
    all forms. A ``status`` query parameter can optionally filter the
    result set.
    """
    def _actor_forms(uid):
        ids = {r['form_id'] for r in approval_records if r['approver_id'] == uid}
        for fid, inst in workflow_instances.items():
            node = inst.current_node()
            if node and (uid in node.approvers or uid in node.delegates):
                ids.add(fid)
        return [f for f in approval_forms if f['id'] in ids]

    scope = request.args.get('scope')
    forms = approval_forms
    if request.user.get('role') == 'admin':
        if scope == 'actor':
            forms = _actor_forms(request.user['id'])
    else:
        if scope == 'actor':
            forms = _actor_forms(request.user['id'])
        else:
            forms = [f for f in forms if f['applicant_id'] == request.user['id']]
    status = request.args.get('status')
    if status:
        forms = [f for f in forms if f.get('status') == status]
    return jsonify(forms)


@bp.post('')
@authenticate_token
def create_form():
    payload = request.get_json() or {}
    form = {
        'id': data['next_id'],
        'data': payload.get('data', {}),
        'template_id': payload.get('template_id'),
        'applicant_id': request.user['id'],
        'org_id': request.user.get('org_id'),
        'dept_id': request.user.get('dept_id'),
        'status': 'draft',
        'submitted_at': None,
        'code': f"APP{data['next_code']:06d}"
    }
    # generate QR code and save path
    os.makedirs('qr_codes', exist_ok=True)
    qr_path = os.path.join('qr_codes', f"{form['code']}.png")
    if qrcode:
        img = qrcode.make(form['code'])
        img.save(qr_path)
    else:  # fallback: create placeholder file
        with open(qr_path, 'wb') as f:  # pragma: no cover
            f.write(b'')
    form['qr_code_path'] = qr_path

    approval_forms.append(form)
    data['next_id'] += 1
    data['next_code'] += 1
    storage.save()
    return jsonify(form), 201


@bp.put('/<int:form_id>')
@authenticate_token
def update_form(form_id):
    form = _find_form(form_id)
    if not form:
        return '', 404
    if form['applicant_id'] != request.user['id'] or form['status'] not in ('draft', 'rejected'):
        return '', 403
    payload = request.get_json() or {}
    if 'data' in payload:
        form['data'] = payload['data']
    storage.save()
    return jsonify(form)


@bp.post('/<int:form_id>/submit')
@authenticate_token
def submit_form(form_id):
    form = _find_form(form_id)
    if not form:
        return '', 404
    now = datetime.utcnow().isoformat()
    form['status'] = 'submitted'
    form['submitted_at'] = now
    record = {
        'id': len(submission_records) + 1,
        'form_id': form_id,
        'submitter_id': request.user['id'],
        'submitted_at': now
    }
    submission_records.append(record)
    tpl = _find_template(form.get('template_id'))
    if tpl:
        wf = Workflow.from_template(tpl.get('steps', []))
        inst = WorkflowInstance(wf)
        workflow_instances[form_id] = inst
        form['status'] = 'in_progress'
    storage.save()
    return jsonify(form)


@bp.post('/<int:form_id>/reject')
@authenticate_token
def reject_form(form_id):
    form = _find_form(form_id)
    if not form:
        return '', 404
    payload = request.get_json() or {}
    now = datetime.utcnow().isoformat()
    sr = _find_submission_record(form_id)
    record = {
        'id': len(approval_records) + 1,
        'form_id': form_id,
        'approver_id': request.user['id'],
        'submission_id': sr['id'] if sr else None,
        'result': 'rejected',
        'comments': payload.get('comments'),
        'attachments': payload.get('attachments', []),
        'acted_at': now,
    }
    approval_records.append(record)
    inst = workflow_instances.get(form_id)
    if inst:
        inst.act(
            actor_id=request.user['id'],
            result='rejected',
            comments=payload.get('comments'),
            attachments=payload.get('attachments'),
        )
        form['status'] = inst.status
    else:
        _after_approval(form, 'rejected')
    resp = dict(form)
    if inst:
        resp['workflow'] = inst.to_dict()
    storage.save()
    return jsonify(resp)


@bp.post('/<int:form_id>/approve')
@authenticate_token
def approve_form(form_id):
    form = _find_form(form_id)
    if not form:
        return '', 404
    payload = request.get_json() or {}
    now = datetime.utcnow().isoformat()
    sr = _find_submission_record(form_id)
    record = {
        'id': len(approval_records) + 1,
        'form_id': form_id,
        'approver_id': request.user['id'],
        'submission_id': sr['id'] if sr else None,
        'result': 'approved',
        'comments': payload.get('comments'),
        'attachments': payload.get('attachments', []),
        'acted_at': now,
    }
    approval_records.append(record)
    inst = workflow_instances.get(form_id)
    if inst:
        inst.act(
            actor_id=request.user['id'],
            result='approved',
            comments=payload.get('comments'),
            attachments=payload.get('attachments'),
        )
        form['status'] = inst.status if inst.status != 'pending' else 'in_progress'
    else:
        _after_approval(form, 'approved')
    resp = dict(form)
    if inst:
        resp['workflow'] = inst.to_dict()
    storage.save()
    return jsonify(resp)


@bp.get('/<int:form_id>')
@authenticate_token
def get_form(form_id):
    form = _find_form(form_id)
    if not form:
        return '', 404
    inst = workflow_instances.get(form_id)
    resp = dict(form)
    if inst:
        resp['workflow'] = inst.to_dict()
    return jsonify(resp)
