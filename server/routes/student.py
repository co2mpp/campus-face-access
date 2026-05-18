"""学生管理 API"""
from flask import Blueprint, request, jsonify
from server.services.student_service import StudentService

bp = Blueprint('student', __name__, url_prefix='/api/student')


def get_service():
    from server.app import SessionLocal
    return StudentService(SessionLocal())


@bp.route('', methods=['POST'])
def create():
    data = request.get_json()
    if not data or 'stu_no' not in data or 'name' not in data:
        return jsonify({'error': '缺少必填字段 stu_no / name'}), 400
    try:
        svc = get_service()
        student = svc.create(
            stu_no=data['stu_no'],
            name=data['name'],
            department=data.get('department')
        )
        return jsonify({
            'id': student.id, 'stu_no': student.stu_no,
            'name': student.name, 'department': student.department,
            'status': student.status
        }), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 409


@bp.route('', methods=['GET'])
def list_students():
    svc = get_service()
    keyword = request.args.get('keyword')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    students, total = svc.list_all(keyword=keyword, page=page, per_page=per_page)
    return jsonify({
        'total': total, 'page': page,
        'data': [{
            'id': s.id, 'stu_no': s.stu_no,
            'name': s.name, 'department': s.department, 'status': s.status
        } for s in students]
    })


@bp.route('/<int:student_id>', methods=['GET'])
def get(student_id):
    svc = get_service()
    s = svc.get_by_id(student_id)
    if not s:
        return jsonify({'error': '学生不存在'}), 404
    return jsonify({
        'id': s.id, 'stu_no': s.stu_no,
        'name': s.name, 'department': s.department, 'status': s.status
    })


@bp.route('/<int:student_id>', methods=['PUT'])
def update(student_id):
    data = request.get_json()
    try:
        svc = get_service()
        allowed = {'stu_no', 'name', 'department'}
        kwargs = {k: v for k, v in data.items() if k in allowed and v is not None}
        s = svc.update(student_id, **kwargs)
        return jsonify({
            'id': s.id, 'stu_no': s.stu_no,
            'name': s.name, 'department': s.department, 'status': s.status
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@bp.route('/<int:student_id>', methods=['DELETE'])
def delete(student_id):
    try:
        svc = get_service()
        svc.delete(student_id)
        return jsonify({'message': '删除成功'})
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
