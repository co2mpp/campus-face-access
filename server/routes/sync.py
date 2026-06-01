"""人脸库同步 API"""
from flask import Blueprint, request, jsonify
from server.services.sync_service import SyncService

bp = Blueprint('sync', __name__, url_prefix='/api/sync')


def get_service():
    from server.app import SessionLocal
    return SyncService(SessionLocal())


@bp.route('/features', methods=['GET'])
def sync_features():
    """
    增量同步人脸特征库
    GET /api/sync/features?since_version=0  (0=全量)
    """
    svc = get_service()
    try:
        since = request.args.get('since_version', 0, type=int)
        data = svc.get_incremental_features(since)
        return jsonify(data)
    finally:
        svc.session.close()


@bp.route('/version', methods=['GET'])
def get_version():
    svc = get_service()
    try:
        return jsonify({'global_version': svc.get_global_version()})
    finally:
        svc.session.close()
