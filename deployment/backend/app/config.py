"""Application configuration for EduVerify."""

from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DEPLOY_ROOT = BASE_DIR.parent
DATA_DIR = Path(os.getenv("EDUVERIFY_DATA_DIR", str(DEPLOY_ROOT / "data")))
STORAGE_DIR = Path(os.getenv("STORAGE_DIR", str(DATA_DIR / "uploads")))


def _resolve_database() -> tuple[str, Path]:
    """
    Returns (sqlalchemy_url, filesystem_db_path_for_mkdir).
    Accepts either a plain file path or sqlite:///... URL.
    """
    raw = os.getenv("DATABASE_URL", "").strip()
    default_path = DATA_DIR / "eduverify.db"

    if not raw:
        return f"sqlite:///{default_path.as_posix()}", default_path

    if raw.startswith("sqlite:///"):
        # sqlite:///C:/path or sqlite:///relative/path
        path_part = raw[len("sqlite:///") :]
        db_path = Path(path_part)
        return raw, db_path

    if raw.startswith("sqlite://"):
        # unusual forms — keep URL, mkdir DATA_DIR only
        return raw, default_path

    # Treat as filesystem path
    db_path = Path(raw)
    return f"sqlite:///{db_path.as_posix()}", db_path


SQLALCHEMY_DATABASE_URL, DB_PATH = _resolve_database()

DEFAULT_MODEL = DEPLOY_ROOT / "models" / "best_ai_image_detector.pth"
MODEL_PATH = Path(os.getenv("MODEL_PATH", str(DEFAULT_MODEL)))
AI_THRESHOLD = float(os.getenv("AI_THRESHOLD", "0.6"))

SECRET_KEY = os.getenv("SECRET_KEY", "eduverify-dev-secret-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))  # 10 MB
ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000",
    ).split(",")
    if origin.strip()
]

# Risk thresholds (on composite score 0..1)
RISK_MEDIUM = float(os.getenv("RISK_MEDIUM", "0.45"))
RISK_HIGH = float(os.getenv("RISK_HIGH", "0.70"))


def ensure_runtime_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
