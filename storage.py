import json
import os

DATA_FILE = 'data.json'

def _load():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

# shared data dictionary
_data = _load()


def save():
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(_data, f)


def init_defaults():
    """Ensure the data file exists with default structures."""
    if not _data or not _data.get('users'):
        reset_all()


def reset_all():
    _data.clear()
    _data.update({
        'organizations': [{'id': 1, 'name': 'Org1'}],
        'departments': [{'id': 1, 'name': 'Dept1', 'org_id': 1}],
        'users': [
            {'id': 1, 'username': 'admin', 'password': 'admin', 'role': 'admin', 'org_id': 1, 'dept_id': 1},
            {'id': 2, 'username': 'user', 'password': 'user', 'role': 'user', 'org_id': 1, 'dept_id': 1}
        ],
        'templates': [],
        'authorized_verifiers': [1],
        'approval_forms': [],
        'submission_records': [],
        'approval_records': [],
        'verification_records': [],
        'next_id': 1,
        'next_code': 1,
    })
    save()


def data():
    return _data

