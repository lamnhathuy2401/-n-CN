"""Review queue and decisions for lecturers."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import require_roles
from app.models import AuditLog, Course, Review, Submission, SubmissionImage, User
from app.routers.submissions import submission_to_out
from app.schemas import ReviewCreate, SubmissionOut

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


@router.get("/queue", response_model=list[SubmissionOut])
def review_queue(
    user: User = Depends(require_roles("lecturer", "admin")),
    db: Session = Depends(get_db),
):
    q = (
        db.query(Submission)
        .options(
            joinedload(Submission.images).joinedload(SubmissionImage.analysis),
            joinedload(Submission.review),
            joinedload(Submission.student),
            joinedload(Submission.course),
        )
        .filter(Submission.status == "pending_review")
    )
    if user.role == "lecturer":
        course_ids = [c.id for c in db.query(Course).filter(Course.lecturer_id == user.id).all()]
        q = q.filter(Submission.course_id.in_(course_ids or [-1]))
    rows = q.order_by(Submission.overall_risk_score.desc(), Submission.created_at.asc()).all()
    return [submission_to_out(s) for s in rows]


@router.post("/{submission_id}", response_model=SubmissionOut)
def decide_review(
    submission_id: int,
    payload: ReviewCreate,
    user: User = Depends(require_roles("lecturer", "admin")),
    db: Session = Depends(get_db),
):
    sub = (
        db.query(Submission)
        .options(
            joinedload(Submission.images).joinedload(SubmissionImage.analysis),
            joinedload(Submission.review),
            joinedload(Submission.student),
            joinedload(Submission.course),
        )
        .filter(Submission.id == submission_id)
        .first()
    )
    if sub is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    if user.role == "lecturer" and (sub.course is None or sub.course.lecturer_id != user.id):
        raise HTTPException(status_code=403, detail="Not your course")

    if sub.review is None:
        review = Review(
            submission_id=sub.id,
            reviewer_id=user.id,
            decision=payload.decision,
            note=payload.note,
        )
        db.add(review)
    else:
        sub.review.decision = payload.decision
        sub.review.note = payload.note
        sub.review.reviewer_id = user.id
        db.add(sub.review)

    sub.status = payload.decision
    db.add(sub)
    db.add(
        AuditLog(
            actor_id=user.id,
            action="review_decision",
            entity_type="submission",
            entity_id=sub.id,
            detail=json.dumps(
                {"decision": payload.decision, "note": payload.note},
                ensure_ascii=False,
            ),
        )
    )
    db.commit()

    refreshed = (
        db.query(Submission)
        .options(
            joinedload(Submission.images).joinedload(SubmissionImage.analysis),
            joinedload(Submission.review),
            joinedload(Submission.student),
            joinedload(Submission.course),
        )
        .filter(Submission.id == submission_id)
        .first()
    )
    assert refreshed is not None
    return submission_to_out(refreshed)
