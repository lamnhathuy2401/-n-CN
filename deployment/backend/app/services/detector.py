"""Lazy wrapper around AIImageDetector with degraded mode support."""

from __future__ import annotations

from typing import Any

from PIL import Image

from app.config import AI_THRESHOLD, MODEL_PATH


class DetectorService:
    def __init__(self) -> None:
        self.detector = None
        self.error: str | None = None
        self.device: str | None = None
        self._try_load()

    def _try_load(self) -> None:
        try:
            # Import locally so backend can start without torch during pure unit tests of risk engine.
            import sys
            from pathlib import Path

            backend_dir = Path(__file__).resolve().parents[2]
            if str(backend_dir) not in sys.path:
                sys.path.insert(0, str(backend_dir))

            from model_service import AIImageDetector

            self.detector = AIImageDetector(MODEL_PATH)
            self.device = str(self.detector.device)
            self.error = None
        except Exception as exc:  # noqa: BLE001 — degraded startup is intentional
            self.detector = None
            self.device = None
            self.error = str(exc)

    @property
    def loaded(self) -> bool:
        return self.detector is not None

    def predict(self, image: Image.Image, threshold: float | None = None) -> dict[str, Any]:
        thr = AI_THRESHOLD if threshold is None else threshold
        if self.detector is None:
            return {
                "prediction": None,
                "label_id": None,
                "prob_real": None,
                "prob_ai_generated": None,
                "threshold": thr,
                "model_available": False,
                "error": self.error or "Model not loaded",
            }
        result = self.detector.predict(image, threshold=thr)
        result["model_available"] = True
        return result


detector_service = DetectorService()
