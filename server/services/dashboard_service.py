"""仪表盘统计服务"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from server.models import Student, FaceFeature, AccessRecord, Device


class DashboardService:
    def __init__(self, session: Session):
        self.session = session

    def get_stats(self) -> dict:
        """返回仪表盘聚合统计数据"""
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        seven_days_ago = today_start - timedelta(days=6)

        # 学生统计
        total_students = self.session.query(func.count(Student.id)).scalar() or 0
        in_school = self.session.query(func.count(Student.id)).filter(
            Student.status == 'in'
        ).scalar() or 0
        out_school = self.session.query(func.count(Student.id)).filter(
            Student.status == 'out'
        ).scalar() or 0
        registered_faces = self.session.query(func.count(FaceFeature.id)).scalar() or 0

        # 今日通行记录
        today_total = self.session.query(func.count(AccessRecord.id)).filter(
            AccessRecord.record_time >= today_start
        ).scalar() or 0
        today_success = self.session.query(func.count(AccessRecord.id)).filter(
            AccessRecord.record_time >= today_start,
            AccessRecord.result == 'success'
        ).scalar() or 0
        today_fail = self.session.query(func.count(AccessRecord.id)).filter(
            AccessRecord.record_time >= today_start,
            AccessRecord.result == 'fail'
        ).scalar() or 0

        # 设备统计
        total_devices = self.session.query(func.count(Device.id)).scalar() or 0
        online_devices = self.session.query(func.count(Device.id)).filter(
            Device.is_online == True
        ).scalar() or 0

        # 7天趋势
        trend_raw = self.session.query(
            func.date(AccessRecord.record_time).label('date'),
            AccessRecord.direction,
            func.count(AccessRecord.id).label('cnt')
        ).filter(
            AccessRecord.record_time >= seven_days_ago
        ).group_by(
            func.date(AccessRecord.record_time),
            AccessRecord.direction
        ).order_by('date').all()

        trend_map = {}
        for row in trend_raw:
            date_str = str(row.date)
            if date_str not in trend_map:
                trend_map[date_str] = {'date': date_str, 'in_count': 0, 'out_count': 0}
            if row.direction == 'in':
                trend_map[date_str]['in_count'] = row.cnt
            elif row.direction == 'out':
                trend_map[date_str]['out_count'] = row.cnt

        trend_7days = list(trend_map.values())

        # 院系分布
        dept_raw = self.session.query(
            Student.department,
            func.count(Student.id).label('cnt')
        ).group_by(Student.department).order_by(desc('cnt')).all()

        department_distribution = []
        for row in dept_raw:
            department_distribution.append({
                'name': row.department or '未设置',
                'count': row.cnt
            })

        # 最近10条通行记录
        recent_raw = self.session.query(AccessRecord).order_by(
            desc(AccessRecord.record_time)
        ).limit(10).all()

        recent_records = []
        for r in recent_raw:
            recent_records.append({
                'id': r.id,
                'stu_no': r.student.stu_no if r.student else None,
                'name': r.student.name if r.student else '未知',
                'direction': r.direction,
                'result': r.result,
                'similarity': r.similarity,
                'record_time': r.record_time.isoformat() if r.record_time else None,
                'device_sn': r.device_sn,
            })

        return {
            'total_students': total_students,
            'in_school': in_school,
            'out_school': out_school,
            'registered_faces': registered_faces,
            'today_total': today_total,
            'today_success': today_success,
            'today_fail': today_fail,
            'total_devices': total_devices,
            'online_devices': online_devices,
            'trend_7days': trend_7days,
            'department_distribution': department_distribution,
            'recent_records': recent_records,
        }
