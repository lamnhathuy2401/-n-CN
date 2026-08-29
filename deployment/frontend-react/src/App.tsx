import { Navigate, Route, Routes } from "react-router-dom";
import type { ReactElement } from "react";
import { useAuth } from "./auth";
import { AppShell } from "./components/AppShell";
import { DashboardPage } from "./pages/DashboardPage";
import { LoginPage } from "./pages/LoginPage";
import { ReviewQueuePage } from "./pages/ReviewQueuePage";
import { SubmissionDetailPage } from "./pages/SubmissionDetailPage";
import { SubmissionsPage } from "./pages/SubmissionsPage";
import { SubmitPage } from "./pages/SubmitPage";

function Protected({ children }: { children: ReactElement }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="page">Đang tải phiên đăng nhập...</div>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

function RoleRoute({
  roles,
  children,
}: {
  roles: Array<"student" | "lecturer" | "admin">;
  children: ReactElement;
}) {
  const { user } = useAuth();
  if (!user || !roles.includes(user.role)) return <Navigate to="/" replace />;
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <Protected>
            <AppShell />
          </Protected>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="submissions" element={<SubmissionsPage />} />
        <Route path="submissions/:id" element={<SubmissionDetailPage />} />
        <Route
          path="submit"
          element={
            <RoleRoute roles={["student", "admin"]}>
              <SubmitPage />
            </RoleRoute>
          }
        />
        <Route
          path="review"
          element={
            <RoleRoute roles={["lecturer", "admin"]}>
              <ReviewQueuePage />
            </RoleRoute>
          }
        />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
