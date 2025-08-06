from datetime import datetime
import os

try:
    import qrcode
except Exception:  # pragma: no cover - fallback if qrcode isn't installed
    qrcode = None

from flask import Blueprint, jsonify, request

from middleware.auth import authenticate_token

bp = Blueprint('approval', __name__, url_prefix='/approvals')

approval_forms = []
submission_records = []
approval_records = []
verification_records = []
_next_id = 1
_next_code = 1


def reset_data():
    global approval_forms, submission_records, approval_records, verification_records, _next_id, _next_code
    approval_forms = []
    submission_records = []
    approval_records = []
    verification_records = []
    _next_id = 1
    _next_code = 1


def _find_form(form_id):
    return next((f for f in approval_forms if f['id'] == form_id), None)


def _find_submission_record(form_id):
    return next((r for r in submission_records if r['form_id'] == form_id), None)


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


@bp.post('')
@authenticate_token
def create_form():
    global _next_id, _next_code
    payload = request.get_json() or {}
    form = {
        'id': _next_id,
        'data': payload.get('data', {}),
        'applicant_id': request.user['id'],
        'org_id': request.user.get('org_id'),
        'dept_id': request.user.get('dept_id'),
        'status': 'draft',
        'submitted_at': None,
        'code': f'APP{_next_code:06d}'
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
    _next_id += 1
    _next_code += 1
    return jsonify(form), 201


@bp.put('/<int:form_id>')
@authenticate_token
def update_form(form_id):
    form = _find_form(form_id)
    if not form:
        return '', 404
    if form['applicant_id'] != request.user['id'] or form['status'] != 'draft':
        return '', 403
    payload = request.get_json() or {}
    if 'data' in payload:
        form['data'] = payload['data']
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
        'acted_at': now,
    }
    approval_records.append(record)
    _after_approval(form, 'rejected')
    return jsonify(form)


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
        'acted_at': now,
    }
    approval_records.append(record)
    _after_approval(form, 'approved')
    return jsonify(form)
