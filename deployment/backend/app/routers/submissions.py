"""Submission + upload + analysis routes."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session, joinedload

from app.config import ALLOWED_EXTENSIONS, ALLOWED_IMAGE_TYPES, MAX_UPLOAD_BYTES, STORAGE_DIR
from app.database import get_db
from app.deps import get_current_user
from app.models import AnalysisResult, AuditLog, Course, Enrollment, Submission, SubmissionImage, User
from app.schemas import AnalysisOut, ImageOut, ReviewOut, SubmissionOut
from app.services.analysis import analyze_submission

router = APIRouter(prefix="/api/submissions", tags=["submissions"])


def _analysis_to_schema(analysis: AnalysisResult | None) -> AnalysisOut | None:
    if analysis is None:
        return None
    metadata = {}
    signals = []
    if analysis.metadata_json:
        try:
            metadata = json.loads(analysis.metadata_json)
        except json.JSONDecodeError:
            metadata = {}
    if analysis.signals_json:
        try:
            signals = json.loads(analysis.signals_json)
        except json.JSONDecodeError:
            signals = []
    return AnalysisOut(
        prediction=analysis.prediction,
        prob_ai=analysis.prob_ai,
        prob_real=analysis.prob_real,
        threshold_used=analysis.threshold_used,
        model_available=analysis.model_available,
        metadata=metadata,
        risk_score=analysis.risk_score,
        risk_level=analysis.risk_level,
        signals=signals,
    )


def submission_to_out(sub: Submission) -> SubmissionOut:
    images = [
        ImageOut(
            id=img.id,
            original_filename=img.original_filename,
            content_type=img.content_type,
            file_size=img.file_size,
            width=img.width,
            height=img.height,
            analysis=_analysis_to_schema(img.analysis),
        )
        for img in sub.images
    ]
    review = None
    if sub.review is not None:
        review = ReviewOut.model_validate(sub.review)
    return SubmissionOut(
        id=sub.id,
        course_id=sub.course_id,
        student_id=sub.student_id,
        title=sub.title,
        description=sub.description,
        status=sub.status,
        overall_risk_score=sub.overall_risk_score,
        overall_risk_level=sub.overall_risk_level,
        created_at=sub.created_at,
        updated_at=sub.updated_at,
        images=images,
        review=review,
        student_name=sub.student.full_name if sub.student else None,
        course_name=sub.course.name if sub.course else None,
    )


def _load_submission(db: Session, submission_id: int) -> Submission | None:
    return (
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


def _can_view(user: User, sub: Submission) -> bool:
    if user.role == "admin":
        return True
    if user.role == "student" and sub.student_id == user.id:
        return True
    if user.role == "lecturer" and sub.course and sub.course.lecturer_id == user.id:
        return True
    return False


@router.get("", response_model=list[SubmissionOut])
def list_submissions(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(Submission).options(
        joinedload(Submission.images).joinedload(SubmissionImage.analysis),
        joinedload(Submission.review),
        joinedload(Submission.student),
        joinedload(Submission.course),
    )
    if user.role == "student":
        q = q.filter(Submission.student_id == user.id)
    elif user.role == "lecturer":
        course_ids = [c.id for c in db.query(Course).filter(Course.lecturer_id == user.id).all()]
        q = q.filter(Submission.course_id.in_(course_ids or [-1]))
    rows = q.order_by(Submission.created_at.desc()).all()
    return [submission_to_out(s) for s in rows]


@router.get("/{submission_id}", response_model=SubmissionOut)
def get_submission(
    submission_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sub = _load_submission(db, submission_id)
    if sub is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    if not _can_view(user, sub):
        raise HTTPException(status_code=403, detail="Not allowed")
    return submission_to_out(sub)


@router.post("", response_model=SubmissionOut)
async def create_submission(
    course_id: int = Form(...),
    title: str = Form(...),
    description: str | None = Form(None),
    files: list[UploadFile] = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role != "student" and user.role != "admin":
        raise HTTPException(status_code=403, detail="Only students can create submissions")
    if not files:
        raise HTTPException(status_code=400, detail="At least one image is required")

    course = db.query(Course).filter(Course.id == course_id).first()
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")

    student_id = user.id
    if user.role == "admin":
        # Admin can submit on behalf of first enrolled student for demo convenience.
        enrollment = db.query(Enrollment).filter(Enrollment.course_id == course_id).first()
        if enrollment is None:
            raise HTTPException(status_code=400, detail="No enrolled student for this course")
        student_id = enrollment.student_id
    else:
        enrolled = (
            db.query(Enrollment)
            .filter(Enrollment.course_id == course_id, Enrollment.student_id == user.id)
            .first()
        )
        if enrolled is None:
            raise HTTPException(status_code=403, detail="Not enrolled in this course")

    submission = Submission(
        course_id=course_id,
        student_id=student_id,
        title=title.strip(),
        description=description,
        status="submitted",
    )
    db.add(submission)
    db.flush()

    dest_dir = STORAGE_DIR / f"submission_{submission.id}"
    dest_dir.mkdir(parents=True, exist_ok=True)

    for upload in files:
        filename = upload.filename or "image.jpg"
        ext = Path(filename).suffix.lower()
        content_type = (upload.content_type or "").lower()
        if ext not in ALLOWED_EXTENSIONS and content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {filename}")

        raw = await upload.read()
        if not raw:
            raise HTTPException(status_code=400, detail=f"Empty file: {filename}")
        if len(raw) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=400, detail=f"File too large (max {MAX_UPLOAD_BYTES} bytes): {filename}")

        try:
            from io import BytesIO

            with Image.open(BytesIO(raw)) as img:
                img.verify()
            with Image.open(BytesIO(raw)) as img:
                width, height = img.size
        except UnidentifiedImageError as exc:
            raise HTTPException(status_code=400, detail=f"Cannot decode image: {filename}") from exc

        stored_name = f"{uuid.uuid4().hex}{ext or '.jpg'}"
        stored_path = dest_dir / stored_name
        stored_path.write_bytes(raw)

        image_row = SubmissionImage(
            submission_id=submission.id,
            original_filename=filename,
            stored_path=str(stored_path),
            content_type=content_type or None,
            file_size=len(raw),
            width=width,
            height=height,
        )
        db.add(image_row)

    db.add(
        AuditLog(
            actor_id=user.id,
            action="submission_created",
            entity_type="submission",
            entity_id=submission.id,
            detail=json.dumps({"title": title, "files": len(files)}, ensure_ascii=False),
        )
    )
    db.commit()

    sub = _load_submission(db, submission.id)
    assert sub is not None
    analyze_submission(db, sub, actor_id=user.id)
    sub = _load_submission(db, submission.id)
    assert sub is not None
    return submission_to_out(sub)


@router.get("/{submission_id}/images/{image_id}/file")
def get_image_file(
    submission_id: int,
    image_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sub = _load_submission(db, submission_id)
    if sub is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    if not _can_view(user, sub):
        raise HTTPException(status_code=403, detail="Not allowed")
    image = next((i for i in sub.images if i.id == image_id), None)
    if image is None:
        raise HTTPException(status_code=404, detail="Image not found")
    path = Path(image.stored_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File missing on disk")
    return FileResponse(path, media_type=image.content_type or "application/octet-stream", filename=image.original_filename)
