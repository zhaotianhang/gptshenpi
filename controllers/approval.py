from datetime import datetime
from flask import Blueprint, jsonify, request

from middleware.auth import authenticate_token

bp = Blueprint('approval', __name__, url_prefix='/approvals')

approval_forms = []
submission_records = []
_next_id = 1
_next_code = 1

def reset_data():
    global approval_forms, submission_records, _next_id, _next_code
    approval_forms = []
    submission_records = []
    _next_id = 1
    _next_code = 1


def _find_form(form_id):
    return next((f for f in approval_forms if f['id'] == form_id), None)


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
    form['status'] = 'rejected'
    return jsonify(form)
