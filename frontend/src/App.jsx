import React, { Suspense } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

import { useAuth } from "./context/AuthContext";

import Loader from "./components/Loader";

/* PAGES */

import Home from "./pages/Home";
import Login from "./pages/Login";
import Register from "./pages/Register";
import { DemoModeProvider } from "./context/DemoModeContext";

import Dashboard from "./pages/Dashboard";

import ProjectList from "./pages/ProjectList";
import ProjectDetails from "./pages/ProjectDetails";

import SubsidyList from "./pages/SubsidyList";
import SubsidyDetails from "./pages/SubsidyDetails";

import DisbursementTracker from "./pages/DisbursementTracker";

import AuditTrail from "./pages/AuditTrail";

import PublicTransparency from "./pages/PublicTransparency";
import PublicSubsidyDetail from "./pages/PublicSubsidyDetail";

const Investigation = React.lazy(() => import("./pages/Investigation"));
const AdminCreateSubsidy = React.lazy(() => import("./pages/AdminCreateSubsidy"));
const AdminCreateProject = React.lazy(() => import("./pages/AdminCreateProject"));
const AdminCreateDisbursement = React.lazy(() => import("./pages/AdminCreateDisbursement"));
const EditSubsidy = React.lazy(() => import("./pages/EditSubsidy"));
const EditProject = React.lazy(() => import("./pages/EditProject"));
const EditDisbursement = React.lazy(() => import("./pages/EditDisbursement"));
const EditRiskEvent = React.lazy(() => import("./pages/EditRiskEvent"));

/* ---------- ROUTE GUARD ---------- */

function ProtectedRoute({ children }) {

  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <Loader message="Initializing session..." />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;

}

/* ---------- ROLE-BASED ROUTE GUARD ---------- */

function RoleRoute({ children, requiredRoles, fallbackPath = "/dashboard" }) {

  const { isAuthenticated, loading, hasAnyRole } = useAuth();

  if (loading) {
    return <Loader message="Initializing session..." />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // If no specific roles required, allow all authenticated users
  if (!requiredRoles || requiredRoles.length === 0) {
    return children;
  }

  // Check if user has required role
  if (!hasAnyRole(requiredRoles)) {
    return <Navigate to={fallbackPath} replace />;
  }

  return children;

}

/* ---------- APP ---------- */

export default function App() {

  return (

    <DemoModeProvider>
    <ToastContainer position="top-right" autoClose={4000} hideProgressBar={false} newestOnTop closeOnClick pauseOnHover theme="light" />
    <Routes>

      {/* PUBLIC ROUTES */}

      <Route path="/" element={<Home />} />

      <Route path="/login" element={<Login />} />

      <Route path="/register" element={<Register />} />

      <Route path="/transparency" element={<PublicTransparency />} />

      <Route path="/public/subsidies/:id" element={<PublicSubsidyDetail />} />

      <Route
        path="/investigation"
        element={
          <RoleRoute requiredRoles={["admin", "auditor", "media"]}>
            <Suspense fallback={<Loader message="Loading investigation..." />}>
              <Investigation />
            </Suspense>
          </RoleRoute>
        }
      />

      {/* PROTECTED ROUTES */}

      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
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

      {/* ADMIN CREATE ROUTES - Requires admin or government_official role */}

      <Route
        path="/admin/create-subsidy"
        element={
          <RoleRoute requiredRoles={["admin", "government_official"]}>
            <Suspense fallback={<Loader message="Loading..." />}>
              <AdminCreateSubsidy />
            </Suspense>
          </RoleRoute>
        }
      />

      <Route
        path="/admin/create-project"
        element={
          <RoleRoute requiredRoles={["admin", "government_official"]}>
            <Suspense fallback={<Loader message="Loading..." />}>
              <AdminCreateProject />
            </Suspense>
          </RoleRoute>
        }
      />

      <Route
        path="/admin/create-disbursement"
        element={
          <RoleRoute requiredRoles={["admin", "government_official"]}>
            <Suspense fallback={<Loader message="Loading..." />}>
              <AdminCreateDisbursement />
            </Suspense>
          </RoleRoute>
        }
      />

      <Route
        path="/admin/edit-subsidy/:id"
        element={
          <RoleRoute requiredRoles={["admin", "government_official"]}>
            <Suspense fallback={<Loader message="Loading..." />}>
              <EditSubsidy />
            </Suspense>
          </RoleRoute>
        }
      />

      <Route
        path="/admin/edit-project/:id"
        element={
          <RoleRoute requiredRoles={["admin", "government_official"]}>
            <Suspense fallback={<Loader message="Loading..." />}>
              <EditProject />
            </Suspense>
          </RoleRoute>
        }
      />

      <Route
        path="/admin/edit-disbursement/:id"
        element={
          <RoleRoute requiredRoles={["admin", "government_official"]}>
            <Suspense fallback={<Loader message="Loading..." />}>
              <EditDisbursement />
            </Suspense>
          </RoleRoute>
        }
      />

      <Route
        path="/admin/edit-risk-event/:id"
        element={
          <RoleRoute requiredRoles={["admin"]}>
            <Suspense fallback={<Loader message="Loading..." />}>
              <EditRiskEvent />
            </Suspense>
          </RoleRoute>
        }
      />

      {/* FALLBACK */}

      <Route path="*" element={<Navigate to="/" replace />} />

    </Routes>
    </DemoModeProvider>
  );

}