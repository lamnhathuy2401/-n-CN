"""Lightweight image metadata / EXIF analyzer."""

from __future__ import annotations

from typing import Any

from PIL import Image
from PIL.ExifTags import TAGS


def analyze_metadata(image: Image.Image, filename: str, file_size: int) -> dict[str, Any]:
    """Extract basic metadata signals useful for risk scoring."""
    width, height = image.size
    exif_raw = {}
    try:
        raw = image.getexif()
        if raw:
            for tag_id, value in raw.items():
                tag = TAGS.get(tag_id, str(tag_id))
                # Keep values JSON-serializable-ish
                exif_raw[tag] = str(value)[:200]
    except Exception:  # noqa: BLE001
        exif_raw = {}

    has_exif = len(exif_raw) > 0
    camera_make = exif_raw.get("Make")
    camera_model = exif_raw.get("Model")
    software = exif_raw.get("Software")
    datetime_original = exif_raw.get("DateTimeOriginal") or exif_raw.get("DateTime")

    suspicious_software = False
    if software:
        soft_l = software.lower()
        keywords = ("midjourney", "stable diffusion", "dall", "generative", "ai")
        suspicious_software = any(k in soft_l for k in keywords)

    return {
        "filename": filename,
        "file_size": file_size,
        "width": width,
        "height": height,
        "format": image.format,
        "mode": image.mode,
        "has_exif": has_exif,
        "camera_make": camera_make,
        "camera_model": camera_model,
        "software": software,
        "datetime_original": datetime_original,
        "suspicious_software": suspicious_software,
        "exif_keys": sorted(exif_raw.keys())[:30],
    }
