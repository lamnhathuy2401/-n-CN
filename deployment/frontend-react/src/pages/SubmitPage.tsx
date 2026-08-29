import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { createSubmission, fetchCourses } from "../api";
import { useAuth } from "../auth";
import type { Course } from "../types";

export function SubmitPage() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [courses, setCourses] = useState<Course[]>([]);
  const [courseId, setCourseId] = useState<number | "">("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [files, setFiles] = useState<FileList | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!token) return;
    fetchCourses(token)
      .then((rows) => {
        setCourses(rows);
        if (rows[0]) setCourseId(rows[0].id);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Không tải được khóa học"));
  }, [token]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!token || courseId === "" || !files || files.length === 0) {
      setError("Vui lòng chọn khóa học và ít nhất một ảnh.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const created = await createSubmission(token, {
        courseId: Number(courseId),
        title,
        description,
        files: Array.from(files),
      });
      navigate(`/submissions/${created.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Nộp bài thất bại");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="page">
      <h2>Nộp bài có ảnh</h2>
      <p className="muted">
        Ảnh sẽ được phân tích tự động. Kết quả AI chỉ hỗ trợ giảng viên, không phải phán quyết cuối.
      </p>
      {error && <div className="alert alert-error">{error}</div>}
      <form className="card form-card" onSubmit={onSubmit}>
        <label>
          Khóa học
          <select
            value={courseId}
            onChange={(e) => setCourseId(e.target.value ? Number(e.target.value) : "")}
            required
          >
            <option value="">-- chọn --</option>
            {courses.map((c) => (
              <option key={c.id} value={c.id}>
                {c.code} — {c.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Tiêu đề bài nộp
          <input value={title} onChange={(e) => setTitle(e.target.value)} required />
        </label>
        <label>
          Mô tả
          <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={4} />
        </label>
        <label>
          Ảnh (jpg/png/webp)
          <input
            type="file"
            accept=".jpg,.jpeg,.png,.webp,image/*"
            multiple
            onChange={(e) => setFiles(e.target.files)}
            required
          />
        </label>
        <button className="btn btn-primary" disabled={busy} type="submit">
          {busy ? "Đang phân tích..." : "Nộp bài & phân tích"}
        </button>
      </form>
    </div>
  );
}
