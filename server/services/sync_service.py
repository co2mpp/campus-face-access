"""人脸库同步服务"""
from sqlalchemy.orm import Session
from server.models import FaceFeature, Student, SyncMetadata


class SyncService:
    def __init__(self, session: Session):
        self.session = session

    def get_global_version(self) -> int:
        meta = self.session.query(SyncMetadata).filter(SyncMetadata.id == 1).first()
        if not meta:
            meta = SyncMetadata(id=1, current_feature_version=1)
            self.session.add(meta)
            self.session.commit()
        return meta.current_feature_version

    def get_incremental_features(self, since_version: int) -> dict:
        """
        增量获取特征库
        :param since_version: 客户端上次同步的版本号
        :return: {features: [...], global_version: int}
        """
        if since_version < 1:
            since_version = 0

        results = (
            self.session.query(FaceFeature, Student)
            .join(Student, FaceFeature.student_id == Student.id)
            .filter(FaceFeature.feature_version > since_version)
            .all()
        )

        global_version = self.get_global_version()
        features = []
        for ff, student in results:
            features.append({
                'student_id': student.id,
                'stu_no': student.stu_no,
                'name': student.name,
                'encrypted_feature': ff.encrypted_feature.hex(),
                'iv': ff.iv.hex(),
                'feature_version': ff.feature_version,
            })
        return {'features': features, 'global_version': global_version}

    def get_full_features(self) -> dict:
        """全量同步"""
        return self.get_incremental_features(since_version=0)
