import React from "react";
import { BrowserRouter, Routes, Route, Navigate, useParams } from "react-router-dom";
import Home from "./pages/Home";
import Login from "./pages/Login";
import AdminDashboard from "./pages/AdminDashboard";
import AuditTrail from "./pages/AuditTrail";
import DisbursementTracker from "./pages/DisbursementTracker";
import ProjectList from "./pages/ProjectList";
import ProjectDetails from "./pages/ProjectDetails";
import SubsidyList from "./pages/SubsidyList";
import SubsidyDetails from "./pages/SubsidyDetails";
import useAuth from "./hooks/useAuth";

function ProtectedRoute({ children, adminOnly = false }) {
  const { user, isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (adminOnly && user?.is_admin !== true) {
    return <div className="unauthorized">Access denied</div>;
  }

  return children;
}

function ProjectDetailsWrapper() {
  const { id } = useParams();
  return <ProjectDetails projectId={id} />;
}

function SubsidyDetailsWrapper() {
  const { id } = useParams();
  return <SubsidyDetails subsidyId={id} />;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
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
              <ProjectDetailsWrapper />
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
              <SubsidyDetailsWrapper />
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
        <Route
          path="/disbursements"
          element={
            <ProtectedRoute>
              <DisbursementTracker />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin"
          element={
            <ProtectedRoute adminOnly={true}>
              <AdminDashboard />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;