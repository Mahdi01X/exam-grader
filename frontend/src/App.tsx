import { Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./lib/auth";
import { ToastProvider } from "./components/Toast";
import { Spinner } from "./components/ui";
import Login from "./pages/Login";
import Exams from "./pages/Exams";
import ExamDetail from "./pages/ExamDetail";
import CopyReview from "./pages/CopyReview";
import Layout from "./components/Layout";

function Protected({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading)
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Spinner className="w-6 h-6" />
      </div>
    );
  if (!user) return <Navigate to="/login" replace />;
  return <Layout>{children}</Layout>;
}

export default function App() {
  return (
    <AuthProvider>
      <ToastProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<Protected><Exams /></Protected>} />
          <Route path="/exams/:id" element={<Protected><ExamDetail /></Protected>} />
          <Route path="/copies/:id" element={<Protected><CopyReview /></Protected>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </ToastProvider>
    </AuthProvider>
  );
}
