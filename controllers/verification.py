from datetime import datetime

from flask import Blueprint, jsonify, request

from middleware.auth import authenticate_token
from . import approval

bp = Blueprint('verification', __name__, url_prefix='/verification')


authorized_verifiers = set()


def reset_data():
    global authorized_verifiers
    authorized_verifiers = {1}  # admin can verify by default


reset_data()


def _find_form_by_code(code):
    return next((f for f in approval.approval_forms if f.get('code') == code), None)


def _find_verification_record(form_id):
    return next((r for r in approval.verification_records if r['form_id'] == form_id), None)


@bp.get('/<code>')
@authenticate_token
def get_form(code):
    form = _find_form_by_code(code)
    if not form:
        return '', 404
    return jsonify(form)


@bp.post('/<code>')
@authenticate_token
def verify_form(code):
    form = _find_form_by_code(code)
    if not form:
        return '', 404
    if request.user['id'] not in authorized_verifiers:
        return '', 403
    payload = request.get_json() or {}
    result = payload.get('result', 'verified')
    comments = payload.get('comments')
    now = datetime.utcnow().isoformat()

    record = _find_verification_record(form['id'])
    if record:
        record.update({
            'verifier_id': request.user['id'],
            'status': result,
            'verified_at': now,
            'comments': comments,
        })
    else:
        record = {
            'id': len(approval.verification_records) + 1,
            'form_id': form['id'],
            'verifier_id': request.user['id'],
            'status': result,
            'verified_at': now,
            'comments': comments,
        }
        approval.verification_records.append(record)

    form['status'] = 'verified' if result == 'verified' else 'verification_failed'
    form['verified_at'] = now
    form['verifier_id'] = request.user['id']
    form['verification_comments'] = comments

    return jsonify(record)
