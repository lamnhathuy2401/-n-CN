"""Pydantic schemas for EduVerify API."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: str

    model_config = {"from_attributes": True}


class CourseOut(BaseModel):
    id: int
    code: str
    name: str
    description: str | None = None
    lecturer_id: int

    model_config = {"from_attributes": True}


class AnalysisOut(BaseModel):
    prediction: str | None = None
    prob_ai: float | None = None
    prob_real: float | None = None
    threshold_used: float | None = None
    model_available: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    risk_score: float | None = None
    risk_level: str | None = None
    signals: list[dict[str, Any]] = Field(default_factory=list)


class ImageOut(BaseModel):
    id: int
    original_filename: str
    content_type: str | None = None
    file_size: int
    width: int | None = None
    height: int | None = None
    analysis: AnalysisOut | None = None


class ReviewOut(BaseModel):
    id: int
    reviewer_id: int
    decision: str
    note: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReviewCreate(BaseModel):
    decision: str = Field(..., pattern="^(approved|flagged|needs_clarification)$")
    note: str | None = None


class SubmissionCreate(BaseModel):
    course_id: int
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


class SubmissionOut(BaseModel):
    id: int
    course_id: int
    student_id: int
    title: str
    description: str | None = None
    status: str
    overall_risk_score: float | None = None
    overall_risk_level: str | None = None
    created_at: datetime
    updated_at: datetime
    images: list[ImageOut] = Field(default_factory=list)
    review: ReviewOut | None = None
    student_name: str | None = None
    course_name: str | None = None
    disclaimer: str = (
        "Kết quả AI chỉ là tín hiệu hỗ trợ quyết định, không phải bằng chứng tuyệt đối."
    )


class DashboardStats(BaseModel):
    total_submissions: int
    pending_review: int
    approved: int
    flagged: int
    needs_clarification: int
    high_risk: int
    medium_risk: int
    low_risk: int
    model_loaded: bool


class HealthOut(BaseModel):
    status: str
    model_loaded: bool
    model_path: str
    device: str | None = None
    message: str | None = None
