from datetime import datetime
import csv
import io

from flask import Blueprint, request, jsonify, send_file

from middleware.auth import authenticate_token
from . import approval

try:  # optional excel support
    from openpyxl import Workbook
except Exception:  # pragma: no cover - optional dependency
    Workbook = None

bp = Blueprint('statistics', __name__, url_prefix='/statistics')


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _filter_forms(forms, status=None, start=None, end=None):
    result = []
    for form in forms:
        if status and form.get('status') != status:
            continue
        submitted_at = form.get('submitted_at')
        if start and (not submitted_at or datetime.fromisoformat(submitted_at) < start):
            continue
        if end and (not submitted_at or datetime.fromisoformat(submitted_at) > end):
            continue
        result.append(form)
    return result


def _paginate(items, page, per_page):
    start = (page - 1) * per_page
    end = start + per_page
    return items[start:end]


def _export_approvals(data, fmt):
    headers = ['id', 'code', 'status', 'amount']
    rows = [
        [f.get('id'), f.get('code'), f.get('status'), f.get('data', {}).get('amount')] for f in data
    ]
    if fmt == 'csv':
        sio = io.StringIO()
        writer = csv.writer(sio)
        writer.writerow(headers)
        writer.writerows(rows)
        output = io.BytesIO(sio.getvalue().encode('utf-8'))
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name='approvals.csv',
        )
    if fmt == 'excel':
        if not Workbook:
            return jsonify({'error': 'excel export not supported'}), 501
        wb = Workbook()
        ws = wb.active
        ws.append(headers)
        for row in rows:
            ws.append(row)
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='approvals.xlsx',
        )
    return '', 400


@bp.get('/dashboard')
@authenticate_token
def dashboard_stats():
    """获取仪表板统计数据"""
    forms = approval.approval_forms
    
    # 统计各状态的数量
    status_counts = {}
    total_amount = 0
    
    for form in forms:
        status = form.get('status', 'draft')
        status_counts[status] = status_counts.get(status, 0) + 1
        
        # 计算总金额
        amount = form.get('data', {}).get('totalAmount', 0)
        if isinstance(amount, (int, float)):
            total_amount += amount
    
    return jsonify({
        'pending': status_counts.get('pending', 0) + status_counts.get('in_progress', 0),
        'approved': status_counts.get('approved', 0),
        'rejected': status_counts.get('rejected', 0),
        'totalAmount': total_amount,
        'totalCount': len(forms)
    })


@bp.get('/approvals')
@authenticate_token
def approval_stats():
    status = request.args.get('status')
    start = _parse_date(request.args.get('start_date'))
    end = _parse_date(request.args.get('end_date'))

    filtered = _filter_forms(approval.approval_forms, status, start, end)
    total_amount = sum(f.get('data', {}).get('totalAmount', 0) for f in filtered)

    export = request.args.get('export')
    if export:
        return _export_approvals(filtered, export)

    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    items = _paginate(filtered, page, per_page)

    return jsonify({
        'items': items,
        'total': len(filtered),
        'total_amount': total_amount,
        'page': page,
        'per_page': per_page
    })


def _filter_verifications(records, status=None, start=None, end=None):
    result = []
    for record in records:
        if status and record.get('status') != status:
            continue
        verified_at = record.get('verified_at')
        if start and (not verified_at or datetime.fromisoformat(verified_at) < start):
            continue
        if end and (not verified_at or datetime.fromisoformat(verified_at) > end):
            continue
        result.append(record)
    return result


def _export_verifications(data, fmt):
    headers = ['id', 'form_id', 'status', 'verifier_id', 'verified_at']
    rows = [
        [r.get('id'), r.get('form_id'), r.get('status'), r.get('verifier_id'), r.get('verified_at')] for r in data
    ]
    if fmt == 'csv':
        sio = io.StringIO()
        writer = csv.writer(sio)
        writer.writerow(headers)
        writer.writerows(rows)
        output = io.BytesIO(sio.getvalue().encode('utf-8'))
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name='verifications.csv',
        )
    if fmt == 'excel':
        if not Workbook:
            return jsonify({'error': 'excel export not supported'}), 501
        wb = Workbook()
        ws = wb.active
        ws.append(headers)
        for row in rows:
            ws.append(row)
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='verifications.xlsx',
        )
    return '', 400


@bp.get('/verification')
@authenticate_token
def verification_stats():
    status = request.args.get('status')
    start = _parse_date(request.args.get('start_date'))
    end = _parse_date(request.args.get('end_date'))

    filtered = _filter_verifications(approval.verification_records, status, start, end)

    export = request.args.get('export')
    if export:
        return _export_verifications(filtered, export)

    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    items = _paginate(filtered, page, per_page)

    return jsonify({
        'items': items,
        'total': len(filtered),
        'page': page,
        'per_page': per_page
    })
