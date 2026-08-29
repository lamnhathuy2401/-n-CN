"""Submission analysis orchestration."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image
from sqlalchemy.orm import Session

from app.config import AI_THRESHOLD
from app.models import AnalysisResult, AuditLog, Submission, SubmissionImage
from app.services.detector import detector_service
from app.services.metadata import analyze_metadata
from app.services.risk import aggregate_submission_risk, compute_image_risk


def analyze_submission(db: Session, submission: Submission, actor_id: int | None = None) -> Submission:
    submission.status = "analyzing"
    db.add(submission)
    db.commit()

    scores: list[float] = []
    for image_row in submission.images:
        path = Path(image_row.stored_path)
        with Image.open(path) as img:
            img.load()
            meta = analyze_metadata(img, image_row.original_filename, image_row.file_size)
            image_row.width = meta.get("width")
            image_row.height = meta.get("height")
            pred = detector_service.predict(img, threshold=AI_THRESHOLD)

        risk = compute_image_risk(
            prob_ai=pred.get("prob_ai_generated"),
            model_available=bool(pred.get("model_available")),
            metadata=meta,
        )
        scores.append(risk["risk_score"])

        analysis = image_row.analysis
        if analysis is None:
            analysis = AnalysisResult(image_id=image_row.id)
            db.add(analysis)

        analysis.prediction = pred.get("prediction")
        analysis.prob_ai = pred.get("prob_ai_generated")
        analysis.prob_real = pred.get("prob_real")
        analysis.threshold_used = pred.get("threshold")
        analysis.model_available = bool(pred.get("model_available"))
        analysis.metadata_json = json.dumps(meta, ensure_ascii=False)
        analysis.risk_score = risk["risk_score"]
        analysis.risk_level = risk["risk_level"]
        analysis.signals_json = json.dumps(risk["signals"], ensure_ascii=False)

    overall = aggregate_submission_risk(scores)
    submission.overall_risk_score = overall["overall_risk_score"]
    submission.overall_risk_level = overall["overall_risk_level"]

    # Auto-approve only low risk; everything else goes to human review.
    if submission.overall_risk_level == "low":
        submission.status = "approved"
    else:
        submission.status = "pending_review"

    db.add(
        AuditLog(
            actor_id=actor_id,
            action="submission_analyzed",
            entity_type="submission",
            entity_id=submission.id,
            detail=json.dumps(
                {
                    "overall_risk_score": submission.overall_risk_score,
                    "overall_risk_level": submission.overall_risk_level,
                    "status": submission.status,
                    "model_loaded": detector_service.loaded,
                },
                ensure_ascii=False,
            ),
        )
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission
