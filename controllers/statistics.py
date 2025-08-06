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


@bp.get('/approvals')
@authenticate_token
def approval_stats():
    status = request.args.get('status')
    start = _parse_date(request.args.get('start_date'))
    end = _parse_date(request.args.get('end_date'))

    filtered = _filter_forms(approval.approval_forms, status, start, end)
    total_amount = sum(f.get('data', {}).get('amount', 0) for f in filtered)

    export = request.args.get('export')
    if export:
        return _export_approvals(filtered, export)

    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    items = _paginate(filtered, page, per_page)

    return jsonify(
        {
            'total': len(filtered),
            'page': page,
            'per_page': per_page,
            'total_amount': total_amount,
            'items': items,
        }
    )


def _filter_verifications(records, status=None, start=None, end=None):
    result = []
    for record in records:
        if status and record.get('status') != status:
            continue
        acted_at = record.get('verified_at')
        if start and (not acted_at or datetime.fromisoformat(acted_at) < start):
            continue
        if end and (not acted_at or datetime.fromisoformat(acted_at) > end):
            continue
        form = next((f for f in approval.approval_forms if f['id'] == record['form_id']), {})
        merged = dict(record)
        merged['amount'] = form.get('data', {}).get('amount', 0)
        result.append(merged)
    return result


def _export_verifications(data, fmt):
    headers = ['id', 'form_id', 'status', 'verified_at', 'amount']
    rows = [[r.get(h) for h in headers] for r in data]
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
    total_amount = sum(r.get('amount', 0) for r in filtered)

    export = request.args.get('export')
    if export:
        return _export_verifications(filtered, export)

    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    items = _paginate(filtered, page, per_page)

    return jsonify(
        {
            'total': len(filtered),
            'page': page,
            'per_page': per_page,
            'total_amount': total_amount,
            'items': items,
        }
    )
