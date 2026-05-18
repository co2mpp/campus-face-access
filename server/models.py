"""MySQL 数据模型定义（smart_gate 数据库）"""
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Enum as SAEnum,
    DateTime, ForeignKey, UniqueConstraint, CheckConstraint,
    Boolean, LargeBinary
)
from sqlalchemy.orm import declarative_base, relationship
from server.config import SQLALCHEMY_DATABASE_URI

Base = declarative_base()


class Student(Base):
    __tablename__ = 'student'

    id = Column(Integer, primary_key=True, autoincrement=True)
    stu_no = Column(String(32), nullable=False, unique=True, comment='学号')
    name = Column(String(64), nullable=False, comment='姓名')
    department = Column(String(128), default=None, comment='院系')
    status = Column(
        SAEnum('in', 'out', name='student_status'),
        nullable=False, default='out', comment='在校状态'
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    face_feature = relationship(
        'FaceFeature', back_populates='student',
        cascade='all, delete-orphan', uselist=False
    )
    access_records = relationship(
        'AccessRecord', back_populates='student',
        foreign_keys='AccessRecord.student_id'
    )


class FaceFeature(Base):
    __tablename__ = 'face_feature'

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(
        Integer, ForeignKey('student.id', ondelete='CASCADE'),
        nullable=False, unique=True, comment='学生ID'
    )
    encrypted_feature = Column(LargeBinary, nullable=False, comment='AES-GCM加密特征(含认证标签)')
    iv = Column(LargeBinary(12), nullable=False, comment='12字节初始化向量')
    feature_version = Column(Integer, nullable=False, index=True, comment='版本号')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student = relationship('Student', back_populates='face_feature')


class AccessRecord(Base):
    __tablename__ = 'access_record'

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(
        Integer, ForeignKey('student.id', ondelete='SET NULL'),
        default=None, comment='学生ID（删除学生后保留记录）'
    )
    device_sn = Column(String(64), nullable=False, index=True, comment='设备序列号')
    direction = Column(
        SAEnum('in', 'out', 'manual', name='direction_type'),
        nullable=False, comment='进出方向'
    )
    result = Column(
        SAEnum('success', 'fail', name='result_type'),
        nullable=False, comment='识别结果'
    )
    similarity = Column(Float, default=None, comment='相似度得分 0~1')
    record_time = Column(DateTime, nullable=False, index=True, comment='识别时间')
    created_at = Column(DateTime, default=datetime.utcnow, comment='入库时间')

    student = relationship(
        'Student', back_populates='access_records',
        foreign_keys=[student_id]
    )


class SyncMetadata(Base):
    __tablename__ = 'sync_metadata'

    id = Column(Integer, primary_key=True, default=1)
    current_feature_version = Column(Integer, nullable=False, default=1, comment='全局特征版本号')

    __table_args__ = (
        CheckConstraint('id = 1', name='ck_sync_metadata_single_row'),
    )


class Device(Base):
    __tablename__ = 'device'

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_sn = Column(String(64), nullable=False, unique=True, comment='设备序列号')
    device_name = Column(String(128), default=None, comment='设备名称')
    last_heartbeat = Column(DateTime, default=None, comment='最后心跳时间')
    is_online = Column(Boolean, default=False, comment='在线状态')
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    """创建所有表"""
    engine = create_engine(SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    return engine


engine = None  # 延迟初始化，在 app.py 中赋值
