"""人脸注册服务"""
import struct
import numpy as np
from sqlalchemy.orm import Session
from server.models import FaceFeature, SyncMetadata
from server.config import AES_KEY
from shared.crypto import encrypt_feature


class FaceService:
    def __init__(self, session: Session):
        self.session = session

    def register(self, student_id: int, embedding: np.ndarray) -> FaceFeature:
        """
        注册人脸特征
        :param student_id: 学生ID
        :param embedding: 512维 float32 特征向量 (normed)
        :return: FaceFeature 记录
        """
        if embedding.shape != (512,):
            raise ValueError(f"特征维度错误: {embedding.shape}")

        feature_bytes = embedding.astype(np.float32).tobytes()
        iv, ciphertext = encrypt_feature(feature_bytes, AES_KEY)

        # 递增全局版本号
        sync_meta = self.session.query(SyncMetadata).filter(SyncMetadata.id == 1).first()
        if not sync_meta:
            sync_meta = SyncMetadata(id=1, current_feature_version=1)
            self.session.add(sync_meta)
            self.session.flush()
        sync_meta.current_feature_version += 1
        new_version = sync_meta.current_feature_version

        # 删除旧特征（如存在）
        self.session.query(FaceFeature).filter(
            FaceFeature.student_id == student_id
        ).delete()

        # 创建新记录
        face_feature = FaceFeature(
            student_id=student_id,
            encrypted_feature=ciphertext,
            iv=iv,
            feature_version=new_version
        )
        self.session.add(face_feature)
        self.session.commit()
        return face_feature

    def get_feature(self, student_id: int) -> FaceFeature | None:
        return self.session.query(FaceFeature).filter(
            FaceFeature.student_id == student_id
        ).first()

    def delete_feature(self, student_id: int) -> None:
        self.session.query(FaceFeature).filter(
            FaceFeature.student_id == student_id
        ).delete()
        self.session.commit()

    @staticmethod
    def feature_to_bytes(embedding: np.ndarray) -> bytes:
        return embedding.astype(np.float32).tobytes()

    @staticmethod
    def bytes_to_feature(data: bytes) -> np.ndarray:
        return np.frombuffer(data, dtype=np.float32)
