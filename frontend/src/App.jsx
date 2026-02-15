import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Home from "./pages/Home";
import Login from "./pages/Login";
import AdminDashboard from "./pages/AdminDashboard";
import ProjectList from "./pages/ProjectList";
import ProjectDetails from "./pages/ProjectDetails";
import SubsidyList from "./pages/SubsidyList";
import SubsidyDetails from "./pages/SubsidyDetails";
import DisbursementTracker from "./pages/DisbursementTracker";
import AuditTrail from "./pages/AuditTrail";
import useAuth from "./hooks/useAuth";

function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) return null;

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />

        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <AdminDashboard />
            </ProtectedRoute>
          }
        />

        <Route
          path="/projects"
          element={
            <ProtectedRoute>
              <ProjectList />
            </ProtectedRoute>
          }
        />

        <Route
          path="/projects/:id"
          element={
            <ProtectedRoute>
              <ProjectDetails />
            </ProtectedRoute>
          }
        />

        <Route
          path="/subsidies"
          element={
            <ProtectedRoute>
              <SubsidyList />
            </ProtectedRoute>
          }
        />

        <Route
          path="/subsidies/:id"
          element={
            <ProtectedRoute>
              <SubsidyDetails />
            </ProtectedRoute>
          }
        />

        <Route
          path="/disbursements"
          element={
            <ProtectedRoute>
              <DisbursementTracker />
            </ProtectedRoute>
          }
        />

        <Route
          path="/audits"
          element={
            <ProtectedRoute>
              <AuditTrail />
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
