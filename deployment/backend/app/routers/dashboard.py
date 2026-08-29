"""Dashboard stats."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Course, Submission, User
from app.schemas import DashboardStats
from app.services.detector import detector_service

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def stats(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(Submission)
    if user.role == "student":
        q = q.filter(Submission.student_id == user.id)
    elif user.role == "lecturer":
        course_ids = [c.id for c in db.query(Course).filter(Course.lecturer_id == user.id).all()]
        q = q.filter(Submission.course_id.in_(course_ids or [-1]))

    rows = q.all()
    return DashboardStats(
        total_submissions=len(rows),
        pending_review=sum(1 for r in rows if r.status == "pending_review"),
        approved=sum(1 for r in rows if r.status == "approved"),
        flagged=sum(1 for r in rows if r.status == "flagged"),
        needs_clarification=sum(1 for r in rows if r.status == "needs_clarification"),
        high_risk=sum(1 for r in rows if r.overall_risk_level == "high"),
        medium_risk=sum(1 for r in rows if r.overall_risk_level == "medium"),
        low_risk=sum(1 for r in rows if r.overall_risk_level == "low"),
        model_loaded=detector_service.loaded,
    )
