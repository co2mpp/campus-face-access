"""仪表盘统计 API"""
from flask import Blueprint, jsonify
from server.services.dashboard_service import DashboardService
from server.routes.auth import login_required

bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')


def get_service():
    from server.app import SessionLocal
    return DashboardService(SessionLocal())


@bp.route('/stats', methods=['GET'])
@login_required
def stats():
    """获取仪表盘聚合统计数据"""
    svc = get_service()
    try:
        data = svc.get_stats()
        return jsonify(data)
    finally:
        svc.session.close()
