"""管理员认证 API"""
import os
from functools import wraps
from flask import Blueprint, request, jsonify, session

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# 管理员凭据，通过环境变量配置，提供默认值仅用于开发环境
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')


def login_required(f):
    """登录验证装饰器，用于保护需要认证的 API 端点"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('authenticated'):
            return jsonify({'error': '未登录'}), 401
        return f(*args, **kwargs)
    return decorated


@bp.route('/login', methods=['POST'])
def login():
    """管理员登录"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': '缺少请求体'}), 400

    username = data.get('username', '')
    password = data.get('password', '')

    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session['authenticated'] = True
        return jsonify({'success': True, 'message': '登录成功'})

    return jsonify({'success': False, 'message': '用户名或密码错误'}), 401


@bp.route('/logout', methods=['POST'])
def logout():
    """管理员登出"""
    session.clear()
    return jsonify({'success': True})


@bp.route('/status', methods=['GET'])
def status():
    """查询当前认证状态"""
    return jsonify({'authenticated': bool(session.get('authenticated'))})
