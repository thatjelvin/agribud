from __future__ import annotations

import hashlib
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class VisionDiagnosis(Base):
    __tablename__ = "vision_diagnoses"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    farm_id: Mapped[UUID | None] = mapped_column(ForeignKey("farms.id"), nullable=True)
    image_hash: Mapped[str] = mapped_column(String(64), index=True)
    diagnosis: Mapped[str] = mapped_column(String(80))
    confidence: Mapped[float] = mapped_column(Float)
    recommended_actions: Mapped[str] = mapped_column(Text)
    model_version: Mapped[str] = mapped_column(String(64))
    extra: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


_DIAGNOSES: list[tuple[str, str, str]] = [
    (
        "leaf_spot_septoria",
        "Suspected Septoria leaf spot (fungal). Confirms a humid microclimate with poor air circulation.",
        "Remove affected leaves, increase spacing, apply copper-based fungicide within 48h.",
    ),
    (
        "nitrogen_deficiency",
        "Visible nitrogen deficiency (uniform yellowing of older leaves).",
        "Apply 30-50 kg/ha of urea; verify with a soil nitrogen test before next application.",
    ),
    (
        "healthy",
        "No visible disease or stress indicators.",
        "Maintain current irrigation and fertilisation schedule; re-photograph in 7 days.",
    ),
    (
        "powdery_mildew",
        "Powdery mildew detected on upper leaf surfaces.",
        "Apply sulphur or potassium bicarbonate spray; reduce overhead irrigation.",
    ),
    (
        "water_stress",
        "Leaf curling and dull green colour consistent with water stress.",
        "Irrigate within 24h; check soil moisture at 30 cm depth.",
    ),
]


def diagnose_from_hash(image_hash: str) -> tuple[str, float, str, str]:
    """Deterministic MVP diagnosis. Production swaps in a CNN/inference call."""
    digest = int(hashlib.sha256(image_hash.encode("utf-8")).hexdigest(), 16)
    diagnosis, message, action = _DIAGNOSES[digest % len(_DIAGNOSES)]
    confidence = 0.62 + ((digest >> 8) % 33) / 100.0
    return diagnosis, round(confidence, 3), message, action
