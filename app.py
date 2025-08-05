from flask import Flask, request, jsonify

from middleware.auth import generate_token, authenticate_token, authorize_roles

app = Flask(__name__)


def reset_data():
    global organizations, departments, users
    organizations = [{'id': 1, 'name': 'Org1'}]
    departments = [{'id': 1, 'name': 'Dept1', 'org_id': 1}]
    users = [
        {'id': 1, 'username': 'admin', 'password': 'admin', 'role': 'admin', 'org_id': 1, 'dept_id': 1},
        {'id': 2, 'username': 'user', 'password': 'user', 'role': 'user', 'org_id': 1, 'dept_id': 1}
    ]


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


if __name__ == '__main__':
    app.run(port=3000)
