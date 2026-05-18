"""心跳监控 API"""
from datetime import datetime
from flask import Blueprint, request, jsonify
from server.models import Device

bp = Blueprint('heartbeat', __name__, url_prefix='/api/heartbeat')


@bp.route('', methods=['POST'])
def heartbeat():
    """接收客户端心跳，更新设备状态"""
    data = request.get_json() or {}
    device_sn = data.get('device_sn', 'unknown')
    from server.app import SessionLocal
    session = SessionLocal()
    try:
        device = session.query(Device).filter(Device.device_sn == device_sn).first()
        if device:
            device.last_heartbeat = datetime.utcnow()
            device.is_online = True
        else:
            device = Device(
                device_sn=device_sn,
                device_name=data.get('device_name', device_sn),
                last_heartbeat=datetime.utcnow(),
                is_online=True
            )
            session.add(device)
        session.commit()
        return jsonify({'status': 'ok'})
    finally:
        session.close()


@bp.route('/status', methods=['GET'])
def device_status():
    from server.app import SessionLocal
    session = SessionLocal()
    try:
        devices = session.query(Device).all()
        return jsonify({
            'devices': [{
                'device_sn': d.device_sn,
                'device_name': d.device_name,
                'last_heartbeat': d.last_heartbeat.isoformat() if d.last_heartbeat else None,
                'is_online': d.is_online,
            } for d in devices]
        })
    finally:
        session.close()
