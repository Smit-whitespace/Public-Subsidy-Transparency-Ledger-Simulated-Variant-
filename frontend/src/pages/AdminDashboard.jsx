import React from "react";
import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";
import DataTable from "../components/DataTable";
import AuditTimeline from "../components/AuditTimeline";
import Loader from "../components/Loader";
import { fetchAudits } from "../api/audit";
import useAuth from "../hooks/useAuth";
import useFetch from "../hooks/useFetch";

export default function AdminDashboard() {
  const { user, isAuthenticated, token } = useAuth();

  const { data, loading, error } = useFetch(
    () => fetchAudits({ limit: 10, offset: 0, token }),
    { immediate: true }
  );

  if (!isAuthenticated || !user || user.is_admin !== true) {
    return <div className="admin-dashboard unauthorized">Access denied</div>;
  }

  if (loading) {
    return <Loader message="Loading admin dashboard..." />;
  }

  if (error) {
    return (
      <div className="admin-dashboard error">Failed to load admin data</div>
    );
  }

  const audits = data?.data || data || [];

  const columns = [
    {
      key: "action",
      label: "Action",
      render: (row) => row.action || "N/A"
    },
    {
      key: "entity",
      label: "Entity",
      render: (row) => row.entity || "N/A"
    },
    {
      key: "entity_id",
      label: "Entity ID",
      render: (row) => row.entity_id || "N/A"
    },
    {
      key: "actor",
      label: "Actor",
      render: (row) => row.performed_by || "system"
    },
    {
      key: "timestamp",
      label: "Timestamp",
      render: (row) => {
        try {
          return new Date(row.timestamp).toLocaleString();
        } catch (_) {
          return row.timestamp || "N/A";
        }
      }
    }
  ];

  return (
    <div className="admin-dashboard">
      <Navbar user={user} />
      <div className="admin-layout">
        <Sidebar user={user} />
        <main className="admin-content">
          <h1>Admin Dashboard</h1>
          <p>System-wide oversight and audit visibility</p>

          <section>
            <h2>Recent Audit Trail</h2>
            <AuditTimeline audits={audits} />
          </section>

          <section>
            <h2>Audit Records</h2>
            <DataTable columns={columns} data={audits} />
          </section>
        </main>
      </div>
    </div>
  );
}