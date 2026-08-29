"""EduVerify FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS, ensure_runtime_dirs
from app.database import Base, SessionLocal, engine
from app.routers import auth, courses, dashboard, health, reviews, submissions
from app.seed import seed_demo_data
from app.services.detector import detector_service

ensure_runtime_dirs()
Base.metadata.create_all(bind=engine)

with SessionLocal() as db:
    seed_demo_data(db)


@asynccontextmanager
async def lifespan(_: FastAPI):
    status = "loaded" if detector_service.loaded else f"degraded ({detector_service.error})"
    print(f"EduVerify started | model: {status}")
    yield


app = FastAPI(
    title="EduVerify API",
    description=(
        "Hệ thống hỗ trợ giảng viên sàng lọc ảnh trong bài nộp sinh viên. "
        "Model AI-vs-Real chỉ là một tín hiệu rủi ro, không phải bằng chứng tuyệt đối."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if CORS_ORIGINS != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(courses.router)
app.include_router(submissions.router)
app.include_router(reviews.router)
app.include_router(dashboard.router)
