# Checklist kiến thức nhóm EduVerify (4 thành viên)

Đề tài: *Ứng dụng Deep Learning xây dựng phần mềm phân loại ảnh AI chống gian lận trong học tập*

**Nguyên tắc phân công**
- **Lý thuyết (mục A):** cả 4 người học chung, ai cũng trả lời được khi hội đồng hỏi tổng quan.
- **Code (mục B–E):** mỗi người **sở hữu** một nhánh; phải đọc được file, giải thích luồng, demo được phần mình.

Điền tên thành viên 4 vào ô `[Tên TV4]` trước khi dùng.

| Vai trò code | Thành viên | Phạm vi chính |
|---|---|---|
| **B** — ML Pipeline | Lâm Nhật Huy | Notebook, huấn luyện, checkpoint, `report_assets/` |
| **C** — Backend API | Quang | FastAPI, JWT, DB, submission/review, integration test |
| **D** — AI Analysis | [Tên TV4] | Detector, metadata, risk engine, `analyze_submission` |
| **E** — Frontend & Ops | Cường | React UI, `api.ts`, README chạy hệ thống, demo |

---

## A. Kiến thức chung — cả 4 người (lý thuyết + demo tổng)

### A1. Câu chuyện đề tài
- [ ] Nêu đúng tên đề tài (phần mềm · phân loại ảnh AI · chống gian lận học tập).
- [ ] EduVerify = tên phần mềm; không đồng nhất với tiêu đề đề tài dài trên bìa.
- [ ] Hai lớp: (1) ResNet50 + xử lý mất cân bằng + threshold; (2) workflow HITL trong phần mềm.
- [ ] Phần mềm **hỗ trợ sàng lọc**, không tự kết luận gian lận.

### A2. Thuật ngữ thống nhất
- [ ] Real / AI (Label_A); **P(AI)**; **AI_THRESHOLD = 0,60**; **risk score R**; HITL.
- [ ] FP / FN và ý nghĩa nghiệp vụ trong giáo dục.
- [ ] Degraded mode khi model không load được.

### A3. Số liệu báo cáo
- [ ] Subset **28k / 6k / 30k**; AI ~83% train.
- [ ] Epoch **7**, val loss **0,0580**; threshold **0,60**.
- [ ] Test: Acc **94,81%**, BalAcc **95,24%**, Macro F1 **0,9142**, Real Recall **0,9590**.

### A4. Giới hạn (nói thật)
- [ ] Subset + một seed; chưa ablation/calibration đầy đủ; risk heuristic; Grad-CAM chưa trên UI.

### A5. Luồng hệ thống end-to-end (ai cũng vẽ được sơ đồ 1 phút)
- [ ] Sinh viên nộp ảnh → backend lưu → detector + metadata → risk → trạng thái bài nộp.
- [ ] Giảng viên review queue → approved / flagged / needs_clarification.
- [ ] UI: **% P(AI)** ≠ **% risk**.

---

## B. Lâm Nhật Huy — ML Pipeline (code)

**File / thư mục phụ trách**
- `AI_Image_Detection(result).ipynb`
- `report_assets/` (biểu đồ, ảnh minh họa xuất từ notebook)
- Checkpoint `.pth` (đường dẫn cấu hình trong `deployment/backend/app/config.py`)

### B1. Notebook — dữ liệu
- [ ] Biết cách load Defactify (Hugging Face); chỉ dùng **Label_A**.
- [ ] Giải thích subset 28k/6k/30k và seed 42.
- [ ] Code tạo `WeightedRandomSampler` (trọng số nghịch đảo tần suất).
- [ ] `NUM_WORKERS=0` trên Colab — vì sao đặt trong code.

### B2. Notebook — tiền xử lý
- [ ] `train_transform` vs `eval_transform`: aug chỉ trên train.
- [ ] Resize 224, ImageNet mean/std — **khớp** với `detector.py` backend.
- [ ] `BinaryDataset` / mapping `(image, label)`.

### B3. Notebook — mô hình & huấn luyện
- [ ] ResNet50 pretrained; freeze đến layer3; head mới + Dropout.
- [ ] BCEWithLogitsLoss; early stopping; lưu checkpoint theo val loss.
- [ ] Đọc được training curves trong `report_assets/training_curves.png`.

### B4. Notebook — đánh giá & threshold
- [ ] Hàm quét threshold trên **validation** (ưu tiên Macro F1).
- [ ] Chọn **0,60**; đánh giá test **một lần**.
- [ ] Xuất confusion matrix, metric, ảnh mẫu dự đoán (`cell_25_*.png`).

### B5. Bàn giao sang backend
- [ ] Checkpoint đặt đúng path mà `DetectorService` / `config.py` đọc.
- [ ] `AI_THRESHOLD=0.60` đồng bộ notebook ↔ `.env` ↔ backend.
- [ ] Preprocessing inference **giống** eval_transform (ảnh hưởng trực tiếp kết quả production).

### B6. Demo / Q&A code (Huy)
- [ ] Mở notebook (hoặc slide) chỉ đúng cell: sampler, threshold, metric cuối.
- [ ] Trả lời: đổi threshold/aug trong notebook mà không sửa backend → sai kết quả live.

**Câu hỏi code hay gặp**
- [ ] Sửa `mean/std` ở đâu? Ảnh hưởng file backend nào?
- [ ] Retrain xong cần copy file gì, restart service gì?

---

## C. Quang — Backend API & nghiệp vụ (code)

**File / thư mục phụ trách**
- `deployment/backend/main.py`
- `deployment/backend/app/auth.py`, `deps.py`, `database.py`, `models.py`, `schemas.py`, `seed.py`
- `deployment/backend/app/routers/` → `auth.py`, `submissions.py`, `reviews.py`, `courses.py`, `dashboard.py`
- `deployment/backend/tests/test_api.py`, `conftest.py`

### C1. Khởi động & cấu hình
- [ ] `main.py`: mount router, CORS, lifespan (log trạng thái model).
- [ ] `config.py`: biến môi trường quan trọng (JWT, DB path, model path — biết chỗ đọc, không nhất thiết sửa).
- [ ] `database.py` + `models.py`: bảng User, Course, Submission, SubmissionImage, Review, AuditLog (nêu được quan hệ).

### C2. Xác thực & phân quyền
- [ ] `auth.py`: hash password, tạo/verify JWT.
- [ ] `deps.py`: `get_current_user`, kiểm tra role (student / lecturer / admin).
- [ ] Endpoint login trả token; client gửi `Authorization: Bearer ...`.

### C3. Vòng đời bài nộp (router `submissions.py`)
- [ ] `POST /api/submissions`: multipart (course_id, title, files).
- [ ] Lưu file local + record DB → gọi `analyze_submission` (biết **điểm gọi**, chi tiết AI do TV4).
- [ ] Trạng thái: submitted → analyzing → approved / pending_review.
- [ ] Chính sách auto-approve khi risk thấp (đọc điều kiện trong code).

### C4. Review & dashboard
- [ ] `reviews.py`: hàng đợi, quyết định giảng viên, ghi audit.
- [ ] `dashboard.py` / `courses.py`: endpoint giảng viên & admin cần cho UI.
- [ ] Schema request/response trong `schemas.py` khớp frontend `types.ts`.

### C5. Kiểm thử tích hợp
- [ ] Chạy: `cd deployment/backend && pytest`
- [ ] `test_api.py`: login, phân quyền, tạo submission, review queue, health.
- [ ] Giải thích 2–3 test cụ thể (setup → assert gì).

### C6. Demo / Q&A code (Quang)
- [ ] Swagger `/docs`: demo login + POST submission (hoặc curl).
- [ ] Trả lời: sinh viên có xem được bài người khác không? (theo query + role trong code).

**Câu hỏi code hay gặp**
- [ ] Thêm trạng thái submission mới sửa file nào?
- [ ] Audit log ghi ở đâu, khi nào?

---

## D. [Tên TV4] — AI Analysis & Risk (code)

**File / thư mục phụ trách**
- `deployment/backend/app/services/detector.py`
- `deployment/backend/app/services/metadata.py`
- `deployment/backend/app/services/risk.py`
- `deployment/backend/app/services/analysis.py`
- `deployment/backend/model_service.py` (nếu dùng)
- `deployment/backend/app/routers/health.py`
- `deployment/backend/tests/test_risk.py`

### D1. Detector service
- [ ] Load checkpoint ResNet50; head khớp kiến trúc notebook.
- [ ] Pipeline: PIL/RGB → tensor → normalize → `sigmoid` → **P(AI)**.
- [ ] So sánh P(AI) với `AI_THRESHOLD` → nhãn Real/AI.
- [ ] **Degraded mode**: không load được model → flag + hành vi fallback (không crash API).

### D2. Metadata analyzer
- [ ] Đọc EXIF: camera, software, kích thước file.
- [ ] Cờ `missing_exif`, `missing_camera`, `suspicious_software` (biết rule trong code).
- [ ] Giới hạn: metadata có thể thiếu/giả — chỉ là tín hiệu phụ.

### D3. Risk engine (`risk.py`)
- [ ] Hàm tính **R** — thuộc công thức và hệ số trong code:
  - `0.75 * P(AI)` (+ metadata flags)
  - model unavailable → `+0.35` thay cho khối P(AI)
- [ ] Map R → low / medium / high (ngưỡng **0.45**, **0.70**).
- [ ] `test_risk.py`: case điển hình đã test (đọc và chạy được).

### D4. Orchestration (`analysis.py`)
- [ ] `analyze_submission` / `analyze_image`: thứ tự gọi detector → metadata → risk.
- [ ] Lưu kết quả vào `SubmissionImage` (prob_ai, risk_score, risk_level, signals…).
- [ ] **Worst-image escalate**: `max(risk)` cấp submission — tìm đúng dòng code.

### D5. Health endpoint
- [ ] `GET /api/health` (hoặc tương đương): báo model loaded / degraded.
- [ ] Giải thích response khi thiếu file `.pth`.

### D6. Demo / Q&A code (TV4)
- [ ] Gọi health → chỉ trạng thái model.
- [ ] Nộp 1 ảnh thiếu EXIF + 1 ảnh AI: chỉ ra risk tăng vì flag nào trong JSON response.

**Câu hỏi code hay gặp**
- [ ] Đổi hệ số risk sửa file nào? Có cần sửa test không?
- [ ] P(AI) và R khác nhau ở bước code nào?

---

## E. Cường — Frontend & triển khai (code)

**File / thư mục phụ trách**
- `deployment/frontend-react/src/` (toàn bộ)
- `deployment/frontend-react/index.html`, `vite.config.ts`
- `deployment/frontend/streamlit_app.py` (nếu còn demo phụ)
- `deployment/README.md`, `deployment/.env.example`

### E1. Cấu trúc React
- [ ] `main.tsx`, `App.tsx`: routing theo trang.
- [ ] `auth.tsx`: lưu token, context user/role.
- [ ] `api.ts`: base URL, helper gọi API, gắn Bearer token.
- [ ] `types.ts` khớp schema backend.

### E2. Trang theo vai trò
- [ ] `LoginPage.tsx` — đăng nhập, chuyển route theo role.
- [ ] `SubmitPage.tsx` — form multipart nộp bài.
- [ ] `SubmissionsPage.tsx` / `SubmissionDetailPage.tsx` — danh sách & chi tiết ảnh.
- [ ] `ReviewQueuePage.tsx` — giảng viên duyệt.
- [ ] `DashboardPage.tsx` — tổng quan (nếu có).
- [ ] `AppShell.tsx` — nav, logout.

### E3. Hiển thị số liệu (quan trọng khi demo)
- [ ] Component hiển thị **P(AI)** và nhãn Real/AI.
- [ ] Component hiển thị **risk score** + level + breakdown metadata.
- [ ] `AuthImage.tsx` (nếu có): load ảnh có token.

### E4. Vận hành local
- [ ] Đọc và thực hiện `deployment/README.md` từ đầu đến cuối.
- [ ] Chạy backend (uvicorn) + frontend (`npm run dev`).
- [ ] `.env.example`: biến cần copy sang `.env`.
- [ ] `npm run build` production — biết output ở `dist/`.
- [ ] Xử lý lỗi thường gặp: CORS, API chưa chạy, 401 thiếu token.

### E5. Kịch bản demo (Cường điều khiển màn hình)
- [ ] Tài khoản seed từ `seed.py` (biết username/password demo).
- [ ] Kịch bản B: nộp ảnh → pending_review → giảng viên flagged/needs_clarification.
- [ ] Backup video demo nếu live fail.

### E6. Demo / Q&A code (Cường)
- [ ] Chỉ trên UI: field nào map API field nào (`prob_ai`, `risk_score`, …).
- [ ] Trả lời: đổi API URL ở đâu (`api.ts` / env Vite).

**Câu hỏi code hay gặp**
- [ ] Thêm cột hiển thị mới: sửa page nào + type nào?
- [ ] Giảng viên bấm Approve gọi endpoint nào?

---

## F. Giao điểm giữa 4 nhánh (mỗi người phải biết “nối dây”)

| Từ → Đến | Ai bàn giao | Nội dung cần khớp |
|---|---|---|
| Notebook → Detector | Huy → TV4 | `.pth`, arch head, mean/std, threshold |
| Analysis → Submissions | TV4 → Quang | `analyze_submission` được gọi sau upload |
| API → React | Quang → Cường | endpoint, schema, JWT, multipart |
| Health / degraded | TV4 → Cường | UI hiển thị khi model lỗi |

- [ ] Cả 4 người đã chạy **một lần** full flow local trước bảo vệ.
- [ ] Có group chat / note: ai sửa file nào trước khi merge.

---

## G. Checklist buổi bảo vệ (cả nhóm)

### Trước 24 giờ
- [ ] Mỗi người tick xong mục code của mình (B/C/D/E).
- [ ] Mục A — cả 4 người ≥ 80% ô đã tick.
- [ ] Phân slide: mở đầu chung → 4 phần code ngắn → demo Cường → kết chung.

### Phân trả lời Q&A (gợi ý)
| Chủ đề | Người trả lời chính |
|---|---|
| Model, metric, threshold | Huy |
| API, JWT, submission, test | Quang |
| Detector, risk, metadata, health | TV4 |
| UI, demo, chạy hệ thống | Cường |
| Lý thuyết / ý nghĩa nghiệp vụ | Ai hỏi ai trả lời nếu thuộc mục A |

### Trước 1 giờ
- [ ] Backend + frontend chạy; health OK hoặc chủ động nói degraded.
- [ ] Ảnh demo copy sẵn trong máy.

---

## H. Tự chấm nhanh

| Thành viên | Mục phụ trách | Lý thuyết chung (A) | Code riêng | Ghi chú |
|---|---|:---:|:---:|---|
| Huy | B | /2 | /2 | |
| Quang | C | /2 | /2 | |
| [Tên TV4] | D | /2 | /2 | |
| Cường | E | /2 | /2 | |
| Cả nhóm | F–G | — | — | |

\*0 = chưa nói/chưa chạy được · 1 = cần nhìn note · 2 = tự tin

**Sẵn sàng bảo vệ:** mỗi người **A ≥ 1,5** và **mục code riêng ≥ 1,5**.
