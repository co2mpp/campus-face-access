"""人脸注册 API"""
import numpy as np
from flask import Blueprint, request, jsonify
from server.services.student_service import StudentService
from server.services.face_service import FaceService
from server.routes.auth import login_required

bp = Blueprint('face', __name__, url_prefix='/api/face')


def get_services():
    from server.app import SessionLocal, get_insightface_app
    session = SessionLocal()
    return FaceService(session), StudentService(session), get_insightface_app()


@bp.route('/register', methods=['POST'])
@login_required
def register():
    """
    上传学生照片进行人脸注册
    multipart/form-data: student_id + photo file
    """
    student_id = request.form.get('student_id', type=int)
    if not student_id:
        return jsonify({'error': '缺少 student_id'}), 400

    if 'photo' not in request.files:
        return jsonify({'error': '缺少照片文件'}), 400

    face_svc, stu_svc, app = get_services()
    session = face_svc.session  # 三个 service 共享同一个 session

    try:
        student = stu_svc.get_by_id(student_id)
        if not student:
            return jsonify({'error': '学生不存在'}), 404

        # 读取照片
        import cv2
        file = request.files['photo']
        img_bytes = file.read()
        img_array = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if img is None:
            return jsonify({'error': '无法解析图片'}), 400

        # InsightFace 检测 + 特征提取
        faces = app.get(img)
        if len(faces) == 0:
            return jsonify({'error': '未检测到人脸'}), 400
        if len(faces) > 1:
            return jsonify({'error': f'检测到 {len(faces)} 张人脸，请上传单人照片'}), 400

        embedding = faces[0].normed_embedding
        if embedding is None:
            return jsonify({'error': '特征提取失败'}), 500

        try:
            ff = face_svc.register(student_id, embedding)
            return jsonify({
                'message': '注册成功',
                'student_id': student_id,
                'feature_version': ff.feature_version
            })
        except Exception as e:
            return jsonify({'error': f'注册失败: {e}'}), 500
    finally:
        session.close()


@bp.route('/student/<int:student_id>', methods=['DELETE'])
@login_required
def delete_feature(student_id):
    from server.app import SessionLocal
    session = SessionLocal()
    try:
        face_svc = FaceService(session)
        face_svc.delete_feature(student_id)
        return jsonify({'message': '人脸特征已删除'})
    finally:
        session.close()


@bp.route('/student/<int:student_id>', methods=['GET'])
def get_feature(student_id):
    from server.app import SessionLocal
    session = SessionLocal()
    try:
        face_svc = FaceService(session)
        ff = face_svc.get_feature(student_id)
        if not ff:
            return jsonify({'error': '未注册人脸'}), 404
        return jsonify({
            'student_id': ff.student_id,
            'feature_version': ff.feature_version,
            'has_feature': True
        })
    finally:
        session.close()
