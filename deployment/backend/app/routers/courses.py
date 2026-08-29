"""Course routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_roles
from app.models import Course, Enrollment, User
from app.schemas import CourseOut

router = APIRouter(prefix="/api/courses", tags=["courses"])


@router.get("", response_model=list[CourseOut])
def list_courses(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role == "admin":
        return db.query(Course).order_by(Course.id).all()
    if user.role == "lecturer":
        return db.query(Course).filter(Course.lecturer_id == user.id).order_by(Course.id).all()
    # student: enrolled courses
    course_ids = [
        e.course_id
        for e in db.query(Enrollment).filter(Enrollment.student_id == user.id).all()
    ]
    if not course_ids:
        return []
    return db.query(Course).filter(Course.id.in_(course_ids)).order_by(Course.id).all()


@router.get("/{course_id}", response_model=CourseOut)
def get_course(
    course_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")

    if user.role == "admin":
        return course
    if user.role == "lecturer" and course.lecturer_id == user.id:
        return course
    if user.role == "student":
        enrolled = (
            db.query(Enrollment)
            .filter(Enrollment.course_id == course_id, Enrollment.student_id == user.id)
            .first()
        )
        if enrolled:
            return course
    raise HTTPException(status_code=403, detail="Not allowed to view this course")
