"""Seed demo users, course, and enrollments."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.auth import get_password_hash
from app.models import Course, Enrollment, User


DEMO_USERS = [
    {
        "email": "admin@eduverify.example",
        "full_name": "System Admin",
        "password": "admin123",
        "role": "admin",
    },
    {
        "email": "lecturer@eduverify.example",
        "full_name": "Giảng viên Demo",
        "password": "lecturer123",
        "role": "lecturer",
    },
    {
        "email": "student@eduverify.example",
        "full_name": "Sinh viên Demo",
        "password": "student123",
        "role": "student",
    },
    {
        "email": "student2@eduverify.example",
        "full_name": "Sinh viên Demo 2",
        "password": "student123",
        "role": "student",
    },
]


def seed_demo_data(db: Session) -> None:
    users_by_email: dict[str, User] = {}
    for item in DEMO_USERS:
        user = db.query(User).filter(User.email == item["email"]).first()
        if user is None:
            user = User(
                email=item["email"],
                full_name=item["full_name"],
                hashed_password=get_password_hash(item["password"]),
                role=item["role"],
            )
            db.add(user)
            db.flush()
        users_by_email[item["email"]] = user

    lecturer = users_by_email["lecturer@eduverify.example"]
    course = db.query(Course).filter(Course.code == "DS445E").first()
    if course is None:
        course = Course(
            code="DS445E",
            name="Đồ án chuyên ngành Khoa học Dữ liệu",
            description="Khóa học demo EduVerify — sàng lọc ảnh trong bài nộp sinh viên.",
            lecturer_id=lecturer.id,
        )
        db.add(course)
        db.flush()

    for email in ("student@eduverify.example", "student2@eduverify.example"):
        student = users_by_email[email]
        exists = (
            db.query(Enrollment)
            .filter(Enrollment.course_id == course.id, Enrollment.student_id == student.id)
            .first()
        )
        if exists is None:
            db.add(Enrollment(course_id=course.id, student_id=student.id))

    db.commit()
