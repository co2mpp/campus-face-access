"""设备管理服务"""
from sqlalchemy.orm import Session
from server.models import Device


class DeviceService:
    def __init__(self, session: Session):
        self.session = session

    def list_all(self, page: int = 1, per_page: int = 20) -> tuple:
        """分页查询所有设备"""
        q = self.session.query(Device)
        total = q.count()
        devices = q.order_by(Device.id).offset(
            (page - 1) * per_page
        ).limit(per_page).all()
        return devices, total

    def get_by_id(self, device_id: int) -> Device | None:
        """根据ID查询设备"""
        return self.session.query(Device).filter(Device.id == device_id).first()

    def get_by_sn(self, device_sn: str) -> Device | None:
        """根据序列号查询设备"""
        return self.session.query(Device).filter(Device.device_sn == device_sn).first()

    def create(self, device_sn: str, device_name: str = None) -> Device:
        """创建设备，校验 device_sn 唯一性"""
        existing = self.get_by_sn(device_sn)
        if existing:
            raise ValueError(f"设备序列号 {device_sn} 已存在")
        device = Device(
            device_sn=device_sn,
            device_name=device_name or device_sn
        )
        self.session.add(device)
        self.session.commit()
        return device

    def update(self, device_id: int, device_name: str = None) -> Device:
        """更新设备名称"""
        device = self.get_by_id(device_id)
        if not device:
            raise ValueError(f"设备不存在: id={device_id}")
        if device_name is not None:
            device.device_name = device_name
        self.session.commit()
        return device

    def delete(self, device_id: int) -> None:
        """删除设备"""
        device = self.get_by_id(device_id)
        if not device:
            raise ValueError(f"设备不存在: id={device_id}")
        self.session.delete(device)
        self.session.commit()
