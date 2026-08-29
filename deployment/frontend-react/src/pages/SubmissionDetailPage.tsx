import { FormEvent, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchSubmission, submitReview } from "../api";
import { useAuth } from "../auth";
import { AuthImage } from "../components/AuthImage";
import type { Submission } from "../types";
import { formatPct, riskClass, statusLabel } from "../utils";

export function SubmissionDetailPage() {
  const { id } = useParams();
  const { token, user } = useAuth();
  const [sub, setSub] = useState<Submission | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [decision, setDecision] = useState("approved");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!token || !id) return;
    fetchSubmission(token, Number(id))
      .then(setSub)
      .catch((err) => setError(err instanceof Error ? err.message : "Lỗi tải chi tiết"));
  }, [token, id]);

  async function onReview(e: FormEvent) {
    e.preventDefault();
    if (!token || !sub) return;
    setBusy(true);
    setError(null);
    try {
      const updated = await submitReview(token, sub.id, decision, note);
      setSub(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không lưu được quyết định");
    } finally {
      setBusy(false);
    }
  }

  if (!sub && !error) return <div className="page">Đang tải...</div>;
  if (!sub) return <div className="page alert alert-error">{error}</div>;

  const canReview = user?.role === "lecturer" || user?.role === "admin";

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <Link to="/submissions">← Quay lại</Link>
          <h2>{sub.title}</h2>
          <p className="muted">
            {sub.course_name} · {sub.student_name} · {statusLabel(sub.status)}
          </p>
        </div>
        <div className="risk-box">
          <span className={riskClass(sub.overall_risk_level)}>{sub.overall_risk_level}</span>
          <div>{formatPct(sub.overall_risk_score)}</div>
        </div>
      </div>

      <div className="alert alert-info">{sub.disclaimer}</div>
      {error && <div className="alert alert-error">{error}</div>}

      <div className="grid detail-grid">
        {sub.images.map((img) => (
          <div className="card" key={img.id}>
            <AuthImage
              className="preview"
              submissionId={sub.id}
              imageId={img.id}
              alt={img.original_filename}
            />
            <h4>{img.original_filename}</h4>
            {img.analysis && (
              <>
                <p>
                  Dự đoán AI: <strong>{img.analysis.prediction || "N/A"}</strong> (
                  {formatPct(img.analysis.prob_ai)})
                </p>
                <p>
                  Rủi ro ảnh:{" "}
                  <span className={riskClass(img.analysis.risk_level)}>
                    {img.analysis.risk_level}
                  </span>{" "}
                  ({formatPct(img.analysis.risk_score)})
                </p>
                <details>
                  <summary>Tín hiệu & metadata</summary>
                  <ul>
                    {img.analysis.signals.map((s) => (
                      <li key={s.name}>
                        <strong>{s.name}</strong>: {s.message} (+{formatPct(s.contribution)})
                      </li>
                    ))}
                  </ul>
                  <pre className="meta-pre">{JSON.stringify(img.analysis.metadata, null, 2)}</pre>
                </details>
              </>
            )}
          </div>
        ))}
      </div>

      {sub.review && (
        <div className="card">
          <h3>Quyết định đã lưu</h3>
          <p>
            {statusLabel(sub.review.decision)} — {sub.review.note || "(không có ghi chú)"}
          </p>
        </div>
      )}

      {canReview && (
        <form className="card form-card" onSubmit={onReview}>
          <h3>Kiểm duyệt của giảng viên</h3>
          <label>
            Quyết định
            <select value={decision} onChange={(e) => setDecision(e.target.value)}>
              <option value="approved">Chấp nhận</option>
              <option value="flagged">Đánh dấu nghi ngờ</option>
              <option value="needs_clarification">Cần làm rõ với sinh viên</option>
            </select>
          </label>
          <label>
            Ghi chú
            <textarea value={note} onChange={(e) => setNote(e.target.value)} rows={3} />
          </label>
          <button className="btn btn-primary" disabled={busy} type="submit">
            {busy ? "Đang lưu..." : "Lưu quyết định"}
          </button>
        </form>
      )}
    </div>
  );
}
