"""通行记录 API"""
from flask import Blueprint, request, jsonify, Response
from server.services.record_service import RecordService

bp = Blueprint('record', __name__, url_prefix='/api/record')


def get_service():
    from server.app import SessionLocal
    return RecordService(SessionLocal())


@bp.route('', methods=['POST'])
def create_record():
    """接收单条通行记录"""
    data = request.get_json()
    if not data:
        return jsonify({'error': '缺少请求体'}), 400
    try:
        svc = get_service()
        record = svc.create(
            student_id=data.get('student_id'),
            device_sn=data.get('device_sn', 'unknown'),
            direction=data['direction'],
            result=data['result'],
            record_time=data.get('record_time'),
            similarity=data.get('similarity')
        )
        return jsonify({
            'id': record.id,
            'student_id': record.student_id,
            'direction': record.direction,
            'result': record.result,
        }), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@bp.route('/batch', methods=['POST'])
def batch_create():
    """批量接收通行记录（客户端断网重传）"""
    data = request.get_json()
    if not data or 'records' not in data:
        return jsonify({'error': '缺少 records 字段'}), 400
    try:
        svc = get_service()
        created = svc.batch_create(data['records'])
        return jsonify({'count': len(created)})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@bp.route('', methods=['GET'])
def query_records():
    """查询通行记录"""
    svc = get_service()
    records, total = svc.query(
        stu_no=request.args.get('stu_no'),
        direction=request.args.get('direction'),
        result=request.args.get('result'),
        device_sn=request.args.get('device_sn'),
        start_time=request.args.get('start_time'),
        end_time=request.args.get('end_time'),
        page=request.args.get('page', 1, type=int),
        per_page=request.args.get('per_page', 20, type=int),
    )
    return jsonify({'total': total, 'data': records})


@bp.route('/<int:record_id>', methods=['DELETE'])
def delete_record(record_id):
    """删除单条通行记录"""
    svc = get_service()
    if svc.delete(record_id):
        return jsonify({'message': '已删除'})
    return jsonify({'error': '记录不存在'}), 404


@bp.route('/export', methods=['GET'])
def export_csv():
    """导出通行记录CSV"""
    svc = get_service()
    csv_data = svc.export_csv(
        stu_no=request.args.get('stu_no'),
        direction=request.args.get('direction'),
        device_sn=request.args.get('device_sn'),
        start_time=request.args.get('start_time'),
        end_time=request.args.get('end_time'),
    )
    return Response(
        csv_data, mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=records.csv'}
    )
