"""Unit tests for risk scoring engine."""

from app.services.risk import aggregate_submission_risk, compute_image_risk, level_from_score


def test_level_from_score_boundaries():
    assert level_from_score(0.0) == "low"
    assert level_from_score(0.44) == "low"
    assert level_from_score(0.45) == "medium"
    assert level_from_score(0.69) == "medium"
    assert level_from_score(0.70) == "high"


def test_high_ai_probability_raises_risk():
    result = compute_image_risk(
        prob_ai=0.95,
        model_available=True,
        metadata={"has_exif": True, "camera_make": "Canon", "camera_model": "EOS"},
    )
    assert result["risk_level"] in {"medium", "high"}
    assert result["risk_score"] >= 0.45
    assert any(s["name"] == "ai_probability" for s in result["signals"])


def test_missing_exif_adds_signal():
    result = compute_image_risk(
        prob_ai=0.2,
        model_available=True,
        metadata={"has_exif": False, "camera_make": None, "camera_model": None},
    )
    names = {s["name"] for s in result["signals"]}
    assert "missing_exif" in names
    assert "missing_camera" in names


def test_model_unavailable_forces_attention():
    result = compute_image_risk(
        prob_ai=None,
        model_available=False,
        metadata={"has_exif": True, "camera_make": "Apple", "camera_model": "iPhone"},
    )
    assert result["risk_score"] >= 0.35
    assert any(s["name"] == "model_unavailable" for s in result["signals"])


def test_aggregate_uses_worst_image():
    overall = aggregate_submission_risk([0.2, 0.8, 0.4])
    assert overall["overall_risk_score"] == 0.8
    assert overall["overall_risk_level"] == "high"
