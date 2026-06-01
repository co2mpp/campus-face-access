"""设备管理 API"""
from flask import Blueprint, request, jsonify
from server.services.device_service import DeviceService
from server.routes.auth import login_required

bp = Blueprint('device', __name__, url_prefix='/api/device')


def get_service():
    from server.app import SessionLocal
    return DeviceService(SessionLocal())


@bp.route('', methods=['GET'])
def list_devices():
    """分页查询所有设备"""
    svc = get_service()
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        devices, total = svc.list_all(page=page, per_page=per_page)
        return jsonify({
            'total': total,
            'page': page,
            'data': [{
                'id': d.id,
                'device_sn': d.device_sn,
                'device_name': d.device_name,
                'last_heartbeat': d.last_heartbeat.isoformat() if d.last_heartbeat else None,
                'is_online': d.is_online,
                'created_at': d.created_at.isoformat() if d.created_at else None,
            } for d in devices]
        })
    finally:
        svc.session.close()


@bp.route('/<int:device_id>', methods=['GET'])
def get_device(device_id):
    """查询单个设备"""
    svc = get_service()
    try:
        d = svc.get_by_id(device_id)
        if not d:
            return jsonify({'error': '设备不存在'}), 404
        return jsonify({
            'id': d.id,
            'device_sn': d.device_sn,
            'device_name': d.device_name,
            'last_heartbeat': d.last_heartbeat.isoformat() if d.last_heartbeat else None,
            'is_online': d.is_online,
            'created_at': d.created_at.isoformat() if d.created_at else None,
        })
    finally:
        svc.session.close()


@bp.route('', methods=['POST'])
@login_required
def create_device():
    """添加设备"""
    data = request.get_json()
    if not data or 'device_sn' not in data:
        return jsonify({'error': '缺少必填字段 device_sn'}), 400
    svc = get_service()
    try:
        device = svc.create(
            device_sn=data['device_sn'],
            device_name=data.get('device_name')
        )
        return jsonify({
            'id': device.id,
            'device_sn': device.device_sn,
            'device_name': device.device_name,
            'is_online': device.is_online,
        }), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 409
    finally:
        svc.session.close()


@bp.route('/<int:device_id>', methods=['PUT'])
@login_required
def update_device(device_id):
    """更新设备名称"""
    data = request.get_json() or {}
    svc = get_service()
    try:
        device = svc.update(device_id, device_name=data.get('device_name'))
        return jsonify({
            'id': device.id,
            'device_sn': device.device_sn,
            'device_name': device.device_name,
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    finally:
        svc.session.close()


@bp.route('/<int:device_id>', methods=['DELETE'])
@login_required
def delete_device(device_id):
    """删除设备"""
    svc = get_service()
    try:
        svc.delete(device_id)
        return jsonify({'message': '删除成功'})
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    finally:
        svc.session.close()
