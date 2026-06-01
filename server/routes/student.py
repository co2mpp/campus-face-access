"""学生管理 API"""
import csv
import io
from flask import Blueprint, request, jsonify
from server.services.student_service import StudentService
from server.routes.auth import login_required

bp = Blueprint('student', __name__, url_prefix='/api/student')


def get_service():
    from server.app import SessionLocal
    return StudentService(SessionLocal())


@bp.route('', methods=['POST'])
@login_required
def create():
    data = request.get_json()
    if not data or 'stu_no' not in data or 'name' not in data:
        return jsonify({'error': '缺少必填字段 stu_no / name'}), 400
    svc = get_service()
    try:
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
    finally:
        svc.session.close()


@bp.route('/batch', methods=['POST'])
@login_required
def batch_create():
    """批量导入学生（JSON 数组或 CSV 文件上传）"""
    students_list = []

    # 检查是否为 multipart 文件上传
    if 'file' in request.files:
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '未选择文件'}), 400
        try:
            content = file.read()
            # 尝试检测编码
            try:
                text = content.decode('utf-8-sig')
            except UnicodeDecodeError:
                text = content.decode('gbk')
            reader = csv.DictReader(io.StringIO(text))
            for row in reader:
                stu_no = (row.get('stu_no') or row.get('学号') or '').strip()
                name = (row.get('name') or row.get('姓名') or '').strip()
                department = (row.get('department') or row.get('院系') or row.get('系别') or '').strip()
                if stu_no and name:
                    students_list.append({
                        'stu_no': stu_no,
                        'name': name,
                        'department': department or None
                    })
        except Exception as e:
            return jsonify({'error': f'CSV 解析失败: {str(e)}'}), 400
    else:
        # JSON body
        data = request.get_json(silent=True)
        if not data or 'students' not in data:
            return jsonify({'error': '缺少 students 字段或 CSV 文件'}), 400
        students_list = data['students']

    if not students_list:
        return jsonify({'error': '没有可导入的学生数据'}), 400

    success_count = 0
    skipped_count = 0
    errors = []

    svc = get_service()
    try:
        for i, item in enumerate(students_list):
            stu_no = item.get('stu_no', '').strip()
            name = item.get('name', '').strip()
            department = item.get('department', '').strip() or None

            if not stu_no or not name:
                errors.append({'index': i, 'error': '缺少 stu_no 或 name'})
                continue

            try:
                svc.create(stu_no=stu_no, name=name, department=department)
                success_count += 1
            except ValueError as e:
                skipped_count += 1
                errors.append({'index': i, 'stu_no': stu_no, 'error': str(e)})
            except Exception as e:
                skipped_count += 1
                errors.append({'index': i, 'stu_no': stu_no, 'error': str(e)})

        return jsonify({
            'success': success_count,
            'skipped': skipped_count,
            'errors': errors
        }), 201
    finally:
        svc.session.close()


@bp.route('', methods=['GET'])
def list_students():
    svc = get_service()
    try:
        keyword = request.args.get('keyword')
        status = request.args.get('status')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        students, total = svc.list_all(keyword=keyword, status=status, page=page, per_page=per_page)
        return jsonify({
            'total': total, 'page': page,
            'data': [{
                'id': s.id, 'stu_no': s.stu_no,
                'name': s.name, 'department': s.department, 'status': s.status
            } for s in students]
        })
    finally:
        svc.session.close()


@bp.route('/<int:student_id>', methods=['GET'])
def get(student_id):
    svc = get_service()
    try:
        s = svc.get_by_id(student_id)
        if not s:
            return jsonify({'error': '学生不存在'}), 404
        return jsonify({
            'id': s.id, 'stu_no': s.stu_no,
            'name': s.name, 'department': s.department, 'status': s.status
        })
    finally:
        svc.session.close()


@bp.route('/<int:student_id>', methods=['PUT'])
@login_required
def update(student_id):
    data = request.get_json()
    svc = get_service()
    try:
        allowed = {'stu_no', 'name', 'department'}
        kwargs = {k: v for k, v in data.items() if k in allowed and v is not None}
        s = svc.update(student_id, **kwargs)
        return jsonify({
            'id': s.id, 'stu_no': s.stu_no,
            'name': s.name, 'department': s.department, 'status': s.status
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    finally:
        svc.session.close()


@bp.route('/<int:student_id>', methods=['DELETE'])
@login_required
def delete(student_id):
    svc = get_service()
    try:
        svc.delete(student_id)
        return jsonify({'message': '删除成功'})
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    finally:
        svc.session.close()
