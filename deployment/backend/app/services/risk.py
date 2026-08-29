"""Risk scoring engine — combines AI probability + metadata signals."""

from __future__ import annotations

from typing import Any

from app.config import RISK_HIGH, RISK_MEDIUM


def level_from_score(score: float) -> str:
    if score >= RISK_HIGH:
        return "high"
    if score >= RISK_MEDIUM:
        return "medium"
    return "low"


def compute_image_risk(
    *,
    prob_ai: float | None,
    model_available: bool,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    """
    Composite risk in [0, 1].
    AI probability is the primary signal; metadata only adjusts the score.
    """
    signals: list[dict[str, Any]] = []
    score = 0.0

    if model_available and prob_ai is not None:
        # Map AI probability into risk with mild amplification near high confidence.
        ai_component = float(prob_ai)
        score += ai_component * 0.75
        signals.append(
            {
                "name": "ai_probability",
                "value": round(ai_component, 4),
                "weight": 0.75,
                "contribution": round(ai_component * 0.75, 4),
                "message": "Xác suất ảnh do AI tạo (model ResNet50).",
            }
        )
    else:
        # Without model, rely more on metadata and force at least medium attention.
        score += 0.35
        signals.append(
            {
                "name": "model_unavailable",
                "value": True,
                "weight": 0.35,
                "contribution": 0.35,
                "message": "Model chưa sẵn sàng — cần kiểm tra thủ công.",
            }
        )

    if not metadata.get("has_exif", False):
        contrib = 0.12
        score += contrib
        signals.append(
            {
                "name": "missing_exif",
                "value": True,
                "weight": contrib,
                "contribution": contrib,
                "message": "Thiếu EXIF — phổ biến ở ảnh AI hoặc ảnh đã strip metadata.",
            }
        )
    else:
        signals.append(
            {
                "name": "has_exif",
                "value": True,
                "weight": 0.0,
                "contribution": 0.0,
                "message": "Có EXIF metadata.",
            }
        )

    if not metadata.get("camera_make") and not metadata.get("camera_model"):
        contrib = 0.08
        score += contrib
        signals.append(
            {
                "name": "missing_camera",
                "value": True,
                "weight": contrib,
                "contribution": contrib,
                "message": "Không có thông tin máy ảnh / thiết bị chụp.",
            }
        )

    if metadata.get("suspicious_software"):
        contrib = 0.15
        score += contrib
        signals.append(
            {
                "name": "suspicious_software",
                "value": metadata.get("software"),
                "weight": contrib,
                "contribution": contrib,
                "message": "Trường Software gợi ý công cụ generative AI.",
            }
        )

    score = max(0.0, min(1.0, score))
    level = level_from_score(score)
    return {
        "risk_score": round(score, 4),
        "risk_level": level,
        "signals": signals,
    }


def aggregate_submission_risk(image_scores: list[float]) -> dict[str, Any]:
    if not image_scores:
        return {"overall_risk_score": 0.0, "overall_risk_level": "low"}
    # Worst-image policy: one high-risk image escalates the whole submission.
    score = max(image_scores)
    return {
        "overall_risk_score": round(score, 4),
        "overall_risk_level": level_from_score(score),
    }
