from datetime import datetime
import os

try:
    import qrcode
except Exception:  # pragma: no cover - fallback if qrcode isn't installed
    qrcode = None

from flask import Blueprint, jsonify, request

from middleware.auth import authenticate_token
import storage
from workflow import Workflow, WorkflowInstance

bp = Blueprint('approval', __name__, url_prefix='/approvals')

data = storage.data()

# 全局变量
workflow_templates = []
workflow_instances = {}


def _refresh_refs():
    global approval_forms, submission_records, approval_records, verification_records, workflow_templates
    approval_forms = data.setdefault('approval_forms', [])
    submission_records = data.setdefault('submission_records', [])
    approval_records = data.setdefault('approval_records', [])
    verification_records = data.setdefault('verification_records', [])
    workflow_templates = data.setdefault('templates', [])


def reset_data():
    data['approval_forms'] = []
    data['submission_records'] = []
    data['approval_records'] = []
    data['verification_records'] = []
    data['templates'] = []
    data['next_id'] = 1
    data['next_code'] = 1
    # Clear any in-memory workflow instances as well
    workflow_instances.clear()
    _refresh_refs()
    storage.save()


_refresh_refs()


def _find_form(form_id):
    return next((f for f in approval_forms if f['id'] == form_id), None)


def _find_submission_record(form_id):
    return next((r for r in submission_records if r['form_id'] == form_id), None)


def _find_template(template_id):
    return next((t for t in workflow_templates if t['id'] == template_id), None)


def _can_approve(user_id, template):
    """检查用户是否有权限审批"""
    if not template:
        return False
    
    nodes = template.get('workflow_config', {}).get('nodes', [])
    if not nodes:
        nodes = template.get('steps', [])
    for node in nodes:
        if node.get('type') == 'approval':
            # 检查是否是审批人
            if user_id in node.get('approvers', []):
                return True
            # 检查是否是代审批人
            if user_id in node.get('delegates', []):
                return True
    
    return False


@bp.get('')
@authenticate_token
def list_forms():
    """Return approval forms visible to the current user."""
    def _actor_forms(uid):
        # 获取用户需要审批的表单
        actor_forms = []
        for form in approval_forms:
            if form['status'] in ['pending', 'in_progress']:
                template = _find_template(form.get('template_id'))
                if template and _can_approve(uid, template):
                    actor_forms.append(form)
        return actor_forms

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
    
    # 添加分页支持
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 10))
    start = (page - 1) * size
    end = start + size
    
    return jsonify({
        'items': forms[start:end],
        'total': len(forms),
        'page': page,
        'size': size
    })


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
        'code': f"APP{data['next_code']:06d}",
        'created_at': datetime.utcnow().isoformat()
    }
    
    # 生成二维码
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

    # 创建工作流实例
    template = _find_template(form.get('template_id'))
    steps = None
    if template:
        steps = template.get('steps')
        if not steps:
            steps = template.get('workflow_config', {}).get('nodes')
    if steps:
        wf = Workflow.from_template(steps)
        inst = WorkflowInstance(wf, context=form.get('data'))
        workflow_instances[form_id] = inst
        node = inst.current_node()
        if node and node.type == 'approval':
            form['status'] = 'in_progress'

    storage.save()
    return jsonify(form)


@bp.post('/<int:form_id>/reject')
@authenticate_token
def reject_form(form_id):
    form = _find_form(form_id)
    if not form:
        return '', 404
    
    # 检查用户是否有权限审批
    template = _find_template(form.get('template_id'))
    if template and not _can_approve(request.user['id'], template):
        return '', 403
    
    payload = request.get_json() or {}
    now = datetime.utcnow().isoformat()
    
    sr = _find_submission_record(form_id)
    attachments = payload.get('attachments', [])
    comments = payload.get('comments')

    inst = workflow_instances.get(form_id)
    if inst:
        inst.act(
            actor_id=request.user['id'],
            result='rejected',
            comments=comments,
            attachments=attachments,
        )
        form['status'] = inst.status
    else:
        form['status'] = 'rejected'

    record = {
        'id': len(approval_records) + 1,
        'form_id': form_id,
        'approver_id': request.user['id'],
        'submission_id': sr['id'] if sr else None,
        'result': 'rejected',
        'comments': comments,
        'attachments': attachments,
        'acted_at': now,
    }
    approval_records.append(record)

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
    
    # 检查用户是否有权限审批
    template = _find_template(form.get('template_id'))
    if template and not _can_approve(request.user['id'], template):
        return '', 403
    
    payload = request.get_json() or {}
    now = datetime.utcnow().isoformat()
    
    sr = _find_submission_record(form_id)
    attachments = payload.get('attachments', [])
    comments = payload.get('comments')

    inst = workflow_instances.get(form_id)
    if inst:
        inst.act(
            actor_id=request.user['id'],
            result='approved',
            comments=comments,
            attachments=attachments,
        )
        if inst.status == 'approved':
            form['status'] = 'approved'
        elif inst.status == 'rejected':
            form['status'] = 'rejected'
        else:
            form['status'] = 'in_progress'
    else:
        form['status'] = 'approved'

    record = {
        'id': len(approval_records) + 1,
        'form_id': form_id,
        'approver_id': request.user['id'],
        'submission_id': sr['id'] if sr else None,
        'result': 'approved',
        'comments': comments,
        'attachments': attachments,
        'acted_at': now,
    }
    approval_records.append(record)

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

    result = dict(form)
    template = _find_template(form.get('template_id'))
    if template:
        result['template'] = template
        result['can_approve'] = _can_approve(request.user['id'], template)

    inst = workflow_instances.get(form_id)
    if inst:
        result['workflow'] = inst.to_dict()

    return jsonify(result)
