import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchStats } from "../api";
import { useAuth } from "../auth";
import type { DashboardStats } from "../types";

export function DashboardPage() {
  const { token, user } = useAuth();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    fetchStats(token)
      .then(setStats)
      .catch((err) => setError(err instanceof Error ? err.message : "Lỗi tải dashboard"));
  }, [token]);

  return (
    <div className="page">
      <h2>Dashboard</h2>
      <p className="muted">Xin chào {user?.full_name}. Vai trò: {user?.role}.</p>
      {error && <div className="alert alert-error">{error}</div>}
      {stats && (
        <>
          <div className="grid stats-grid">
            <Stat label="Tổng bài nộp" value={stats.total_submissions} />
            <Stat label="Chờ duyệt" value={stats.pending_review} />
            <Stat label="Đã chấp nhận" value={stats.approved} />
            <Stat label="Đánh dấu nghi ngờ" value={stats.flagged} />
            <Stat label="Rủi ro cao" value={stats.high_risk} />
            <Stat label="Rủi ro trung bình" value={stats.medium_risk} />
            <Stat label="Rủi ro thấp" value={stats.low_risk} />
            <Stat label="Model AI" value={stats.model_loaded ? "Sẵn sàng" : "Degraded"} />
          </div>
          <div className="card info-card">
            <h3>Luồng nghiệp vụ</h3>
            <ol>
              <li>Sinh viên nộp bài kèm ảnh minh họa.</li>
              <li>Hệ thống chạy AI Detection + phân tích metadata.</li>
              <li>Risk Engine gán mức low / medium / high.</li>
              <li>Giảng viên duyệt các case medium/high trong hàng đợi.</li>
            </ol>
            {(user?.role === "lecturer" || user?.role === "admin") && (
              <Link className="btn btn-primary" to="/review">
                Mở hàng đợi duyệt
              </Link>
            )}
            {user?.role === "student" && (
              <Link className="btn btn-primary" to="/submit">
                Nộp bài mới
              </Link>
            )}
          </div>
        </>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="card stat-card">
      <div className="muted">{label}</div>
      <div className="stat-value">{value}</div>
    </div>
  );
}
