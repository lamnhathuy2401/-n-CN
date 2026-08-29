import { Link, NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../auth";

export function AppShell() {
  const { user, logout } = useAuth();

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <Link to="/">EduVerify</Link>
          <span className="muted">Sàng lọc ảnh bài nộp</span>
        </div>
        <nav className="nav">
          <NavLink to="/" end>
            Dashboard
          </NavLink>
          <NavLink to="/submissions">Bài nộp</NavLink>
          {user?.role === "student" && <NavLink to="/submit">Nộp bài</NavLink>}
          {(user?.role === "lecturer" || user?.role === "admin") && (
            <NavLink to="/review">Hàng đợi duyệt</NavLink>
          )}
        </nav>
        <div className="userbox">
          <div>
            <strong>{user?.full_name}</strong>
            <div className="muted">{user?.role}</div>
          </div>
          <button className="btn btn-ghost" onClick={logout} type="button">
            Đăng xuất
          </button>
        </div>
      </header>
      <main className="content">
        <Outlet />
      </main>
      <footer className="footer">
        Kết quả AI chỉ hỗ trợ quyết định — giảng viên vẫn chịu trách nhiệm kiểm duyệt cuối cùng.
      </footer>
    </div>
  );
}
