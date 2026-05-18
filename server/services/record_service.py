"""通行记录服务"""
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
from server.models import AccessRecord, Student


class RecordService:
    def __init__(self, session: Session):
        self.session = session

    def create(self, student_id: int | None, device_sn: str,
               direction: str, result: str, record_time: datetime = None,
               similarity: float = None) -> AccessRecord:
        if direction not in ('in', 'out', 'manual'):
            raise ValueError(f"方向非法: {direction}")
        if result not in ('success', 'fail'):
            raise ValueError(f"结果非法: {result}")

        # 校验 student_id 是否有效，无效则置空（客户端可能持有过期数据）
        if student_id:
            student = self.session.query(Student).filter(Student.id == student_id).first()
            if not student:
                student_id = None

        record = AccessRecord(
            student_id=student_id,
            device_sn=device_sn,
            direction=direction,
            result=result,
            similarity=similarity,
            record_time=record_time or datetime.utcnow()
        )
        self.session.add(record)

        # 更新学生在校状态
        if result == 'success' and student_id:
            student = self.session.query(Student).filter(Student.id == student_id).first()
            if student:
                if direction in ('in', 'manual'):
                    student.status = 'in'
                elif direction == 'out':
                    student.status = 'out'

        self.session.commit()
        return record

    def batch_create(self, records: list[dict]) -> list[AccessRecord]:
        """批量创建记录（用于客户端上传）"""
        created = []
        for r in records:
            record_time = r.get('record_time')
            if isinstance(record_time, str):
                record_time = datetime.fromisoformat(record_time)
            elif record_time is None:
                record_time = datetime.utcnow()

            rec = self.create(
                student_id=r.get('student_id'),
                device_sn=r['device_sn'],
                direction=r['direction'],
                result=r['result'],
                record_time=record_time,
                similarity=r.get('similarity')
            )
            created.append(rec)
        return created

    def query(self, stu_no: str = None, direction: str = None,
              result: str = None, device_sn: str = None,
              start_time: str = None, end_time: str = None,
              page: int = 1, per_page: int = 20) -> tuple:
        q = self.session.query(AccessRecord)

        if stu_no:
            q = q.join(Student, AccessRecord.student_id == Student.id).filter(
                Student.stu_no.like(f'%{stu_no}%')
            )
        if direction:
            q = q.filter(AccessRecord.direction == direction)
        if result:
            q = q.filter(AccessRecord.result == result)
        if device_sn:
            q = q.filter(AccessRecord.device_sn.like(f'%{device_sn}%'))
        if start_time:
            q = q.filter(AccessRecord.record_time >= datetime.fromisoformat(start_time))
        if end_time:
            q = q.filter(AccessRecord.record_time <= datetime.fromisoformat(end_time))

        total = q.count()
        records = q.order_by(desc(AccessRecord.record_time)).offset(
            (page - 1) * per_page
        ).limit(per_page).all()

        result_list = []
        for r in records:
            result_list.append({
                'id': r.id,
                'student_id': r.student_id,
                'stu_no': r.student.stu_no if r.student else None,
                'student_name': r.student.name if r.student else None,
                'device_sn': r.device_sn,
                'direction': r.direction,
                'result': r.result,
                'similarity': r.similarity,
                'record_time': r.record_time.isoformat() if r.record_time else None,
            })
        return result_list, total

    def delete(self, record_id: int) -> bool:
        record = self.session.query(AccessRecord).filter(AccessRecord.id == record_id).first()
        if not record:
            return False
        self.session.delete(record)
        self.session.commit()
        return True

    def export_csv(self, **kwargs) -> str:
        """导出CSV"""
        import csv
        import io
        records, _ = self.query(per_page=100000, **kwargs)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', '学号', '姓名', '设备号', '方向', '结果', '相似度', '时间'])
        for r in records:
            writer.writerow([
                r['id'], r['stu_no'], r['student_name'],
                r['device_sn'], r['direction'], r['result'],
                f"{r['similarity']:.2%}" if r['similarity'] else '',
                r['record_time']
            ])
        return output.getvalue()
