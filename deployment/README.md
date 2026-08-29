# EduVerify — Hệ thống sàng lọc ảnh trong bài nộp sinh viên

EduVerify biến model AI-vs-Real thành **một tín hiệu rủi ro** trong quy trình nghiệp vụ giáo dục:
sinh viên nộp bài có ảnh → hệ thống phân tích → giảng viên kiểm duyệt các case đáng ngờ.

## Kiến trúc MVP

```
deployment/
├── backend/                 # FastAPI + SQLite + JWT
│   ├── app/                 # domain, services, routers
│   ├── model_service.py     # ResNet50 detector module
│   ├── main.py              # entrypoint
│   └── tests/
├── frontend-react/          # React + TypeScript (Vite)
├── frontend/                # Streamlit demo cũ (tuỳ chọn)
├── models/                  # đặt best_ai_image_detector.pth vào đây
└── data/                    # SQLite + uploads (runtime)
```

## Tài khoản demo

| Vai trò | Email | Password |
|---------|-------|----------|
| Admin | admin@eduverify.example | admin123 |
| Giảng viên | lecturer@eduverify.example | lecturer123 |
| Sinh viên | student@eduverify.example | student123 |

## 1) Chuẩn bị model

Copy checkpoint từ Google Drive / Colab:

`deployment/models/best_ai_image_detector.pth`

Nếu thiếu file này, API vẫn chạy ở chế độ **degraded** (metadata + human review vẫn hoạt động).

## 2) Chạy backend

```bash
cd deployment/backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Docs: http://127.0.0.1:8000/docs

## 3) Chạy React frontend

```bash
cd deployment/frontend-react
npm install
npm run dev
```

Mở http://127.0.0.1:5173

Vite đã proxy `/api` tới backend `:8000`.

## 4) Luồng nghiệp vụ demo

1. Đăng nhập **student@eduverify.example**
2. Vào **Nộp bài** → chọn khóa DS445E → upload 1–n ảnh
3. Hệ thống chạy AI Detection + EXIF/metadata → gán risk `low|medium|high`
4. Đăng nhập **lecturer@eduverify.example**
5. Vào **Hàng đợi duyệt** → mở case → quyết định `approved / flagged / needs_clarification`

## 5) API chính

- `POST /api/auth/login`
- `GET /api/auth/me`
- `GET /api/courses`
- `POST /api/submissions` (multipart: course_id, title, description, files[])
- `GET /api/submissions`
- `GET /api/submissions/{id}`
- `GET /api/reviews/queue`
- `POST /api/reviews/{id}`
- `GET /api/dashboard/stats`
- `GET /api/health`
- `POST /predict` (legacy, không auth)

## 6) Kiểm thử

```bash
cd deployment/backend
pytest -q
```

## 7) Biến môi trường

Xem [`.env.example`](.env.example).

| Biến | Ý nghĩa |
|------|---------|
| `MODEL_PATH` | Đường dẫn checkpoint |
| `AI_THRESHOLD` | Ngưỡng binary prediction |
| `RISK_MEDIUM` / `RISK_HIGH` | Ngưỡng mức rủi ro tổng hợp |
| `SECRET_KEY` | JWT secret |
| `CORS_ORIGINS` | Origin frontend |

## Nguyên tắc thiết kế

- Model **không** kết luận tuyệt đối “gian lận”.
- Risk Engine kết hợp AI probability + metadata signals.
- Case medium/high luôn vào human review.
- Mọi quyết định kiểm duyệt được ghi audit log.
