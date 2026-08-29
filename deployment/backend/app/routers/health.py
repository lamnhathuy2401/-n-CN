"""Health + legacy predict endpoint."""

from __future__ import annotations

import io

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from PIL import Image, UnidentifiedImageError

from app.config import MODEL_PATH
from app.schemas import HealthOut
from app.services.detector import detector_service

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthOut)
@router.get("/api/health", response_model=HealthOut)
def health():
    return HealthOut(
        status="ok" if detector_service.loaded else "degraded",
        model_loaded=detector_service.loaded,
        model_path=str(MODEL_PATH),
        device=detector_service.device,
        message=None if detector_service.loaded else detector_service.error,
    )


@router.post("/predict")
@router.post("/api/predict")
async def predict_legacy(
    file: UploadFile = File(...),
    threshold: float = Query(0.6, ge=0.05, le=0.95),
):
    """Backward-compatible raw predict endpoint (no auth)."""
    if not detector_service.loaded:
        raise HTTPException(status_code=503, detail=detector_service.error or "Model is not loaded")

    content_type = (file.content_type or "").lower()
    if content_type and not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail=f"Expected an image, got: {content_type}")

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty file")
    try:
        image = Image.open(io.BytesIO(raw))
    except UnidentifiedImageError as exc:
        raise HTTPException(status_code=400, detail="Cannot decode image") from exc

    result = detector_service.predict(image, threshold=threshold)
    result["filename"] = file.filename
    return result
