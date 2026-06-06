"""学生信息管理服务"""
from sqlalchemy.orm import Session
from sqlalchemy import or_
from server.models import Student


class StudentService:
    def __init__(self, session: Session):
        self.session = session

    def create(self, stu_no: str, name: str, department: str = None) -> Student:
        existing = self.session.query(Student).filter(Student.stu_no == stu_no).first()
        if existing:
            raise ValueError(f"学号 {stu_no} 已存在")
        student = Student(stu_no=stu_no, name=name, department=department)
        self.session.add(student)
        self.session.commit()
        return student

    def get_by_id(self, student_id: int) -> Student | None:
        return self.session.query(Student).filter(Student.id == student_id).first()

    def get_by_stu_no(self, stu_no: str) -> Student | None:
        return self.session.query(Student).filter(Student.stu_no == stu_no).first()

    def list_all(self, keyword: str = None, status: str = None, page: int = 1, per_page: int = 20) -> tuple:
        q = self.session.query(Student)
        if keyword:
            q = q.filter(
                or_(
                    Student.name.like(f'%{keyword}%'),
                    Student.stu_no.like(f'%{keyword}%'),
                    Student.department.like(f'%{keyword}%')
                )
            )
        if status and status in ('in', 'out'):
            q = q.filter(Student.status == status)
        total = q.count()
        students = q.order_by(Student.id).offset((page - 1) * per_page).limit(per_page).all()
        return students, total

    def update(self, student_id: int, **kwargs) -> Student:
        student = self.get_by_id(student_id)
        if not student:
            raise ValueError(f"学生不存在: id={student_id}")
        for field, value in kwargs.items():
            if hasattr(student, field) and value is not None:
                setattr(student, field, value)
        self.session.commit()
        return student

    def delete(self, student_id: int) -> None:
        student = self.get_by_id(student_id)
        if not student:
            raise ValueError(f"学生不存在: id={student_id}")
        self.session.delete(student)
        self.session.commit()

    def update_status(self, student_id: int, status: str) -> Student:
        if status not in ('in', 'out'):
            raise ValueError(f"状态值非法: {status}")
        return self.update(student_id, status=status)
