import { FormEvent, useState } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../auth";

const DEMO_ACCOUNTS = [
  { role: "Giảng viên", email: "lecturer@eduverify.example", password: "lecturer123" },
  { role: "Sinh viên", email: "student@eduverify.example", password: "student123" },
  { role: "Admin", email: "admin@eduverify.example", password: "admin123" },
];

export function LoginPage() {
  const { user, login, loading } = useAuth();
  const [email, setEmail] = useState("lecturer@eduverify.example");
  const [password, setPassword] = useState("lecturer123");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (!loading && user) return <Navigate to="/" replace />;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(email, password);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Đăng nhập thất bại");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-page">
      <form className="card login-card" onSubmit={onSubmit}>
        <h1>EduVerify</h1>
        <p className="muted">
          Hệ thống hỗ trợ giảng viên sàng lọc ảnh AI trong bài nộp của sinh viên.
        </p>
        {error && <div className="alert alert-error">{error}</div>}
        <label>
          Email
          <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required />
        </label>
        <label>
          Mật khẩu
          <input
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            type="password"
            required
          />
        </label>
        <button className="btn btn-primary" disabled={busy} type="submit">
          {busy ? "Đang đăng nhập..." : "Đăng nhập"}
        </button>
        <div className="demo-box">
          <strong>Tài khoản demo</strong>
          <ul>
            {DEMO_ACCOUNTS.map((a) => (
              <li key={a.email}>
                <button
                  type="button"
                  className="linkish"
                  onClick={() => {
                    setEmail(a.email);
                    setPassword(a.password);
                  }}
                >
                  {a.role}: {a.email}
                </button>
              </li>
            ))}
          </ul>
        </div>
      </form>
    </div>
  );
}
