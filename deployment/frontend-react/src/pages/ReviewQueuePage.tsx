import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchReviewQueue } from "../api";
import { useAuth } from "../auth";
import type { Submission } from "../types";
import { formatPct, riskClass, statusLabel } from "../utils";

export function ReviewQueuePage() {
  const { token } = useAuth();
  const [rows, setRows] = useState<Submission[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    fetchReviewQueue(token)
      .then(setRows)
      .catch((err) => setError(err instanceof Error ? err.message : "Lỗi tải hàng đợi"));
  }, [token]);

  return (
    <div className="page">
      <h2>Hàng đợi kiểm duyệt</h2>
      <p className="muted">
        Ưu tiên các bài có điểm rủi ro cao. Model chỉ cung cấp tín hiệu — quyết định cuối thuộc về
        giảng viên.
      </p>
      {error && <div className="alert alert-error">{error}</div>}
      <div className="card table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Tiêu đề</th>
              <th>Sinh viên</th>
              <th>Rủi ro</th>
              <th>Điểm</th>
              <th>Trạng thái</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((s) => (
              <tr key={s.id}>
                <td>{s.id}</td>
                <td>{s.title}</td>
                <td>{s.student_name}</td>
                <td>
                  <span className={riskClass(s.overall_risk_level)}>
                    {s.overall_risk_level}
                  </span>
                </td>
                <td>{formatPct(s.overall_risk_score)}</td>
                <td>{statusLabel(s.status)}</td>
                <td>
                  <Link to={`/submissions/${s.id}`}>Mở case</Link>
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td colSpan={7} className="muted">
                  Không có bài nào đang chờ duyệt.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
