import datetime
from functools import wraps

import jwt
from flask import request

SECRET = 'secret'


def generate_token(user):
    payload = {
        'id': user['id'],
        'role': user['role'],
        'org_id': user.get('org_id'),
        'dept_id': user.get('dept_id'),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET, algorithm='HS256')


def authenticate_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.split(' ')[1] if auth_header else None
        if not token:
            return '', 401
        try:
            decoded = jwt.decode(token, SECRET, algorithms=['HS256'])
        except jwt.InvalidTokenError:
            return '', 403
        request.user = decoded
        return f(*args, **kwargs)
    return decorated


def authorize_roles(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not getattr(request, 'user', None) or request.user.get('role') not in roles:
                return '', 403
            return f(*args, **kwargs)
        return decorated
    return decorator
