"""Streamlit UI — gọi FastAPI backend (hoặc fallback load model local)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import requests
import streamlit as st
from PIL import Image

# Cho phép import model_service khi chạy standalone (không qua API)
BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000").rstrip("/")
DEFAULT_MODEL = Path(__file__).resolve().parents[1] / "models" / "best_ai_image_detector.pth"
MODEL_PATH = Path(os.getenv("MODEL_PATH", str(DEFAULT_MODEL)))

st.set_page_config(
    page_title="AI Image Detection",
    page_icon="🔍",
    layout="centered",
)

st.title("AI-Generated Image Detection")
st.caption("ResNet50 · Defactify · Real vs AI-Generated")

mode = st.sidebar.radio(
    "Chế độ inference",
    ["Qua FastAPI", "Local (load .pth trực tiếp)"],
    index=0,
)
threshold = st.sidebar.slider("Ngưỡng AI-Generated", 0.1, 0.9, 0.6, 0.05)
st.sidebar.markdown(f"**API_URL:** `{API_URL}`")
st.sidebar.markdown(f"**MODEL_PATH:** `{MODEL_PATH}`")


@st.cache_resource
def get_local_detector():
    from model_service import AIImageDetector

    return AIImageDetector(MODEL_PATH)


uploaded = st.file_uploader("Tải ảnh lên", type=["jpg", "jpeg", "png", "webp"])

if uploaded is not None:
    image = Image.open(uploaded).convert("RGB")
    st.image(image, caption=uploaded.name, use_container_width=True)

    if st.button("Phân loại", type="primary"):
        with st.spinner("Đang dự đoán..."):
            try:
                if mode == "Qua FastAPI":
                    files = {
                        "file": (uploaded.name, uploaded.getvalue(), uploaded.type or "image/jpeg")
                    }
                    resp = requests.post(
                        f"{API_URL}/predict",
                        params={"threshold": threshold},
                        files=files,
                        timeout=60,
                    )
                    if resp.status_code != 200:
                        st.error(f"API error {resp.status_code}: {resp.text}")
                        st.stop()
                    result = resp.json()
                else:
                    detector = get_local_detector()
                    result = detector.predict(image, threshold=threshold)
            except requests.exceptions.ConnectionError:
                st.error(
                    "Không kết nối được FastAPI. Chạy backend trước:\n\n"
                    "`uvicorn main:app --reload --port 8000` trong thư mục `deployment/backend`"
                )
                st.stop()
            except Exception as exc:
                st.error(f"Lỗi: {exc}")
                st.stop()

        pred = result["prediction"]
        if pred == "AI-Generated":
            st.error(f"Kết quả: **{pred}**")
        else:
            st.success(f"Kết quả: **{pred}**")

        c1, c2 = st.columns(2)
        c1.metric("P(Real)", f"{result['prob_real']:.2%}")
        c2.metric("P(AI-Generated)", f"{result['prob_ai_generated']:.2%}")

        st.progress(
            min(max(result["prob_ai_generated"], 0.0), 1.0),
            text="Xác suất AI-Generated",
        )
else:
    st.info("Upload một ảnh để kiểm tra Real / AI-Generated.")

st.markdown("---")
st.markdown(
    "Backend: FastAPI (`/predict`, `/health`) · "
    "Model checkpoint: `best_ai_image_detector.pth`"
)
