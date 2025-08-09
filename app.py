import werkzeug
if not hasattr(werkzeug, "__version__"):
    werkzeug.__version__ = "3"

from flask import Flask, request, jsonify, send_from_directory

from middleware.auth import generate_token, authenticate_token, authorize_roles
from controllers import approval, verification
from controllers.approval import bp as approval_bp
from controllers.verification import bp as verification_bp
from controllers.statistics import bp as statistics_bp
import storage

app = Flask(__name__)
app.register_blueprint(approval_bp)
app.register_blueprint(verification_bp)
app.register_blueprint(statistics_bp)

storage.init_defaults()
data = storage.data()


@app.get('/admin')
def admin_page():
    return send_from_directory('static', 'admin.html')


def reset_data():
    data['organizations'] = [{'id': 1, 'name': 'Org1'}]
    data['departments'] = [{'id': 1, 'name': 'Dept1', 'org_id': 1}]
    data['users'] = [
        {'id': 1, 'username': 'admin', 'password': 'admin', 'role': 'admin', 'org_id': 1, 'dept_id': 1},
        {'id': 2, 'username': 'user', 'password': 'user', 'role': 'user', 'org_id': 1, 'dept_id': 1}
    ]
    data['templates'] = []
    approval.reset_data()
    verification.reset_data()
    storage.save()

@app.post('/login')
def login():
    payload = request.get_json() or {}
    user = next((u for u in data['users'] if u['username'] == payload.get('username') and u['password'] == payload.get('password')), None)
    if not user:
        return '', 401
    token = generate_token(user)
    return jsonify(token=token)


@app.get('/users/<int:user_id>')
@authenticate_token
def get_user(user_id):
    if request.user['role'] != 'admin' and request.user['id'] != user_id:
        return '', 403
    user = next((u for u in data['users'] if u['id'] == user_id), None)
    if not user:
        return '', 404
    return jsonify(user)


@app.put('/users/<int:user_id>')
@authenticate_token
def update_user(user_id):
    if request.user['role'] != 'admin' and request.user['id'] != user_id:
        return '', 403
    user = next((u for u in data['users'] if u['id'] == user_id), None)
    if not user:
        return '', 404
    user.update(request.get_json() or {})
    storage.save()
    return jsonify(user)


@app.get('/admin/users')
@authenticate_token
@authorize_roles('admin')
def list_users():
    return jsonify(data['users'])


@app.post('/admin/users')
@authenticate_token
@authorize_roles('admin')
def create_user():
    new_user = request.get_json() or {}
    new_user['id'] = max([u['id'] for u in data['users']], default=0) + 1
    data['users'].append(new_user)
    storage.save()
    return jsonify(new_user), 201


@app.put('/admin/users/<int:user_id>')
@authenticate_token
@authorize_roles('admin')
def admin_update_user(user_id):
    user = next((u for u in data['users'] if u['id'] == user_id), None)
    if not user:
        return '', 404
    user.update(request.get_json() or {})
    storage.save()
    return jsonify(user)


@app.delete('/admin/users/<int:user_id>')
@authenticate_token
@authorize_roles('admin')
def delete_user(user_id):
    data['users'] = [u for u in data['users'] if u['id'] != user_id]
    storage.save()
    return '', 204


@app.get('/admin/orgs')
@authenticate_token
@authorize_roles('admin')
def list_orgs():
    return jsonify(data['organizations'])


@app.post('/admin/orgs')
@authenticate_token
@authorize_roles('admin')
def create_org():
    org = request.get_json() or {}
    org['id'] = max([o['id'] for o in data['organizations']], default=0) + 1
    data['organizations'].append(org)
    storage.save()
    return jsonify(org), 201


@app.put('/admin/orgs/<int:org_id>')
@authenticate_token
@authorize_roles('admin')
def update_org(org_id):
    org = next((o for o in data['organizations'] if o['id'] == org_id), None)
    if not org:
        return '', 404
    org.update(request.get_json() or {})
    storage.save()
    return jsonify(org)


@app.delete('/admin/orgs/<int:org_id>')
@authenticate_token
@authorize_roles('admin')
def delete_org(org_id):
    data['organizations'] = [o for o in data['organizations'] if o['id'] != org_id]
    storage.save()
    return '', 204


@app.get('/admin/depts')
@authenticate_token
@authorize_roles('admin')
def list_depts():
    return jsonify(data['departments'])


@app.post('/admin/depts')
@authenticate_token
@authorize_roles('admin')
def create_dept():
    dept = request.get_json() or {}
    dept['id'] = max([d['id'] for d in data['departments']], default=0) + 1
    data['departments'].append(dept)
    storage.save()
    return jsonify(dept), 201


@app.put('/admin/depts/<int:dept_id>')
@authenticate_token
@authorize_roles('admin')
def update_dept(dept_id):
    dept = next((d for d in data['departments'] if d['id'] == dept_id), None)
    if not dept:
        return '', 404
    dept.update(request.get_json() or {})
    storage.save()
    return jsonify(dept)


@app.delete('/admin/depts/<int:dept_id>')
@authenticate_token
@authorize_roles('admin')
def delete_dept(dept_id):
    data['departments'] = [d for d in data['departments'] if d['id'] != dept_id]
    storage.save()
    return '', 204


@app.get('/admin/templates')
@authenticate_token
@authorize_roles('admin')
def list_templates():
    return jsonify(data['templates'])


def _normalize_template(payload, require_config=False):
    """Validate and normalize template structure.

    Accepts either legacy `steps` or new `workflow_config` formats and
    converts them into the standard `workflow_config` structure.
    """
    steps = payload.pop('steps', None)
    if steps is not None:
        payload['workflow_config'] = {'nodes': steps}

    if 'workflow_config' in payload:
        wf_cfg = payload['workflow_config']
        if not isinstance(wf_cfg, dict):
            raise ValueError('workflow_config must be an object')
        nodes = wf_cfg.get('nodes')
        if not isinstance(nodes, list):
            raise ValueError('nodes must be a list')
        for node in nodes:
            if not isinstance(node, dict) or 'id' not in node or 'type' not in node:
                raise ValueError('each node requires id and type')
    elif require_config:
        raise ValueError('workflow_config required')

    return payload


@app.post('/admin/templates')
@authenticate_token
@authorize_roles('admin')
def create_template():
    tpl = request.get_json() or {}
    try:
        tpl = _normalize_template(tpl, require_config=True)
    except ValueError:
        return '', 400
    tpl['id'] = max([t['id'] for t in data['templates']], default=0) + 1
    data['templates'].append(tpl)
    storage.save()
    return jsonify(tpl), 201


@app.put('/admin/templates/<int:template_id>')
@authenticate_token
@authorize_roles('admin')
def update_template(template_id):
    tpl = next((t for t in data['templates'] if t['id'] == template_id), None)
    if not tpl:
        return '', 404
    payload = request.get_json() or {}
    try:
        payload = _normalize_template(payload)
    except ValueError:
        return '', 400
    tpl.update(payload)
    storage.save()
    return jsonify(tpl)


@app.delete('/admin/templates/<int:template_id>')
@authenticate_token
@authorize_roles('admin')
def delete_template(template_id):
    data['templates'] = [t for t in data['templates'] if t['id'] != template_id]
    storage.save()
    return '', 204


@app.get('/admin/verifiers')
@authenticate_token
@authorize_roles('admin')
def list_verifiers():
    return jsonify(sorted(verification.authorized_verifiers))


@app.post('/admin/verifiers')
@authenticate_token
@authorize_roles('admin')
def add_verifier():
    payload = request.get_json() or {}
    uid = payload.get('user_id')
    if uid is None:
        return '', 400
    verification.authorized_verifiers.add(uid)
    data['authorized_verifiers'] = sorted(verification.authorized_verifiers)
    storage.save()
    return jsonify({'user_id': uid}), 201


@app.delete('/admin/verifiers/<int:user_id>')
@authenticate_token
@authorize_roles('admin')
def remove_verifier(user_id):
    verification.authorized_verifiers.discard(user_id)
    data['authorized_verifiers'] = sorted(verification.authorized_verifiers)
    storage.save()
    return '', 204


@app.get('/verify/<code>')
@authenticate_token
def verify_form_by_code(code):
    """通过二维码验证审批单"""
    from controllers.verification import _find_form_by_code
    form = _find_form_by_code(code)
    if not form:
        return '', 404
    return jsonify(form)


if __name__ == '__main__':
    app.run(port=3000)
