import werkzeug
if not hasattr(werkzeug, "__version__"):
    werkzeug.__version__ = "3"

from flask import Flask, request, jsonify, send_from_directory

from middleware.auth import generate_token, authenticate_token, authorize_roles
from controllers import approval, verification
from controllers.approval import bp as approval_bp
from controllers.verification import bp as verification_bp
from controllers.statistics import bp as statistics_bp

app = Flask(__name__)
app.register_blueprint(approval_bp)
app.register_blueprint(verification_bp)
app.register_blueprint(statistics_bp)


@app.get('/admin')
def admin_page():
    return send_from_directory('static', 'admin.html')


def reset_data():
    global organizations, departments, users, templates
    organizations = [{'id': 1, 'name': 'Org1'}]
    departments = [{'id': 1, 'name': 'Dept1', 'org_id': 1}]
    users = [
        {'id': 1, 'username': 'admin', 'password': 'admin', 'role': 'admin', 'org_id': 1, 'dept_id': 1},
        {'id': 2, 'username': 'user', 'password': 'user', 'role': 'user', 'org_id': 1, 'dept_id': 1}
    ]
    templates = []
    approval.reset_data()
    verification.reset_data()


reset_data()


@app.post('/login')
def login():
    data = request.get_json() or {}
    user = next((u for u in users if u['username'] == data.get('username') and u['password'] == data.get('password')), None)
    if not user:
        return '', 401
    token = generate_token(user)
    return jsonify(token=token)


@app.get('/users/<int:user_id>')
@authenticate_token
def get_user(user_id):
    if request.user['role'] != 'admin' and request.user['id'] != user_id:
        return '', 403
    user = next((u for u in users if u['id'] == user_id), None)
    if not user:
        return '', 404
    return jsonify(user)


@app.put('/users/<int:user_id>')
@authenticate_token
def update_user(user_id):
    if request.user['role'] != 'admin' and request.user['id'] != user_id:
        return '', 403
    user = next((u for u in users if u['id'] == user_id), None)
    if not user:
        return '', 404
    user.update(request.get_json() or {})
    return jsonify(user)


@app.get('/admin/users')
@authenticate_token
@authorize_roles('admin')
def list_users():
    return jsonify(users)


@app.post('/admin/users')
@authenticate_token
@authorize_roles('admin')
def create_user():
    new_user = request.get_json() or {}
    new_user['id'] = len(users) + 1
    users.append(new_user)
    return jsonify(new_user), 201


@app.put('/admin/users/<int:user_id>')
@authenticate_token
@authorize_roles('admin')
def admin_update_user(user_id):
    user = next((u for u in users if u['id'] == user_id), None)
    if not user:
        return '', 404
    user.update(request.get_json() or {})
    return jsonify(user)


@app.delete('/admin/users/<int:user_id>')
@authenticate_token
@authorize_roles('admin')
def delete_user(user_id):
    global users
    users = [u for u in users if u['id'] != user_id]
    return '', 204


@app.get('/admin/orgs')
@authenticate_token
@authorize_roles('admin')
def list_orgs():
    return jsonify(organizations)


@app.post('/admin/orgs')
@authenticate_token
@authorize_roles('admin')
def create_org():
    org = request.get_json() or {}
    org['id'] = len(organizations) + 1
    organizations.append(org)
    return jsonify(org), 201


@app.put('/admin/orgs/<int:org_id>')
@authenticate_token
@authorize_roles('admin')
def update_org(org_id):
    org = next((o for o in organizations if o['id'] == org_id), None)
    if not org:
        return '', 404
    org.update(request.get_json() or {})
    return jsonify(org)


@app.delete('/admin/orgs/<int:org_id>')
@authenticate_token
@authorize_roles('admin')
def delete_org(org_id):
    global organizations
    organizations = [o for o in organizations if o['id'] != org_id]
    return '', 204


@app.get('/admin/depts')
@authenticate_token
@authorize_roles('admin')
def list_depts():
    return jsonify(departments)


@app.post('/admin/depts')
@authenticate_token
@authorize_roles('admin')
def create_dept():
    dept = request.get_json() or {}
    dept['id'] = len(departments) + 1
    departments.append(dept)
    return jsonify(dept), 201


@app.put('/admin/depts/<int:dept_id>')
@authenticate_token
@authorize_roles('admin')
def update_dept(dept_id):
    dept = next((d for d in departments if d['id'] == dept_id), None)
    if not dept:
        return '', 404
    dept.update(request.get_json() or {})
    return jsonify(dept)


@app.delete('/admin/depts/<int:dept_id>')
@authenticate_token
@authorize_roles('admin')
def delete_dept(dept_id):
    global departments
    departments = [d for d in departments if d['id'] != dept_id]
    return '', 204


@app.get('/admin/templates')
@authenticate_token
@authorize_roles('admin')
def list_templates():
    return jsonify(templates)


@app.post('/admin/templates')
@authenticate_token
@authorize_roles('admin')
def create_template():
    tpl = request.get_json() or {}
    tpl['id'] = len(templates) + 1
    templates.append(tpl)
    return jsonify(tpl), 201


@app.put('/admin/templates/<int:template_id>')
@authenticate_token
@authorize_roles('admin')
def update_template(template_id):
    tpl = next((t for t in templates if t['id'] == template_id), None)
    if not tpl:
        return '', 404
    tpl.update(request.get_json() or {})
    return jsonify(tpl)


@app.delete('/admin/templates/<int:template_id>')
@authenticate_token
@authorize_roles('admin')
def delete_template(template_id):
    global templates
    templates = [t for t in templates if t['id'] != template_id]
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
    data = request.get_json() or {}
    uid = data.get('user_id')
    if uid is None:
        return '', 400
    verification.authorized_verifiers.add(uid)
    return jsonify({'user_id': uid}), 201


@app.delete('/admin/verifiers/<int:user_id>')
@authenticate_token
@authorize_roles('admin')
def remove_verifier(user_id):
    verification.authorized_verifiers.discard(user_id)
    return '', 204


if __name__ == '__main__':
    app.run(port=3000)
