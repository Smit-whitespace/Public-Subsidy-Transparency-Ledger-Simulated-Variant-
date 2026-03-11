import React, { useCallback } from "react";

import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";
import DataTable from "../components/DataTable";
import AuditTimeline from "../components/AuditTimeline";
import Loader from "../components/Loader";

import KpiCard from "../components/Analytics/KpiCard";
import SectorDistributionChart from "../components/Analytics/SectorDistributionChart";
import RiskDistributionChart from "../components/Analytics/RiskDistributionChart";
import YearTrendChart from "../components/Analytics/YearTrendChart";
import RiskBadge from "../components/RiskBadge";
import TransparencyIndicator from "../components/TransparencyIndicator";

import { useAuth } from "../context/AuthContext";
import useFetch from "../hooks/useFetch";

import {
  getDashboardSummary,
  getSectorDistribution,
  getRiskDistribution,
  getYearTrends,
  getHighRiskSubsidies
} from "../services/analyticsService";

import { getAudits } from "../services/auditService";

import { formatCurrency } from "../utils/formatCurrency";

export default function AdminDashboard() {

  const { user, token, isAuthenticated } = useAuth();

  /* ---------- STABLE FETCH FUNCTIONS ---------- */

  const fetchAudits = useCallback(() => {
    if (!token) return Promise.resolve([]);
    return getAudits(token, 10, 0);
  }, [token]);

  const fetchSummary = useCallback(() => {
    if (!token) return Promise.resolve(null);
    return getDashboardSummary(token);
  }, [token]);

  const fetchSector = useCallback(() => {
    if (!token) return Promise.resolve([]);
    return getSectorDistribution(token);
  }, [token]);

  const fetchRisk = useCallback(() => {
    if (!token) return Promise.resolve([]);
    return getRiskDistribution(token);
  }, [token]);

  const fetchYear = useCallback(() => {
    if (!token) return Promise.resolve([]);
    return getYearTrends(token);
  }, [token]);

  const fetchHighRisk = useCallback(() => {
    if (!token) return Promise.resolve([]);
    return getHighRiskSubsidies(token);
  }, [token]);

  /* ---------- FETCH DATA ---------- */

  const {
    data: auditData,
    loading: auditLoading,
    error: auditError
  } = useFetch(fetchAudits, { immediate: true });

  const {
    data: summary,
    loading: summaryLoading
  } = useFetch(fetchSummary, { immediate: true });

  const {
    data: sectorDistribution,
    loading: sectorLoading
  } = useFetch(fetchSector, { immediate: true });

  const {
    data: riskDistribution,
    loading: riskLoading
  } = useFetch(fetchRisk, { immediate: true });

  const {
    data: yearTrends,
    loading: yearLoading
  } = useFetch(fetchYear, { immediate: true });

  const {
    data: highRisk,
    loading: highRiskLoading
  } = useFetch(fetchHighRisk, { immediate: true });

  /* ---------- AUTH GUARD ---------- */

  if (!isAuthenticated || !user) {
    return (
      <div className="admin-dashboard unauthorized">
        Access denied
      </div>
    );
  }

  const dashboardLoading =
    auditLoading ||
    summaryLoading ||
    sectorLoading ||
    riskLoading ||
    yearLoading ||
    highRiskLoading;

  if (dashboardLoading) {
    return <Loader message="Loading dashboard..." />;
  }

  if (auditError) {
    return (
      <div className="admin-dashboard error">
        Failed to load dashboard
      </div>
    );
  }

  /* ---------- NORMALIZE DATA ---------- */

  const audits = auditData?.data || auditData || [];
  const highRiskSubsidies = highRisk?.data || highRisk || [];

  /* ---------- TABLE CONFIG ---------- */

  const auditColumns = [
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
          return new Date(row.created_at || row.timestamp).toLocaleString();
        } catch {
          return "N/A";
        }
      }
    }
  ];

  const highRiskColumns = [
    {
      key: "title",
      label: "Subsidy"
    },
    {
      key: "recipient",
      label: "Recipient"
    },
    {
      key: "risk_score",
      label: "Risk",
      render: (row) => <RiskBadge score={row.risk_score} />
    },
    {
      key: "transparency_score",
      label: "Transparency",
      render: (row) => (
        <TransparencyIndicator value={row.transparency_score} />
      )
    }
  ];

  /* ---------- RENDER ---------- */

  return (
    <div className="admin-dashboard">

      <Navbar />

      <div className="admin-layout">

        <Sidebar />

        <main className="admin-content">

          <header className="dashboard-header">
            <h1>PSTL Intelligence Dashboard</h1>
            <p>System-wide transparency and subsidy intelligence</p>
          </header>

          {/* KPI STRIP */}

          <section className="dashboard-kpis">

            <KpiCard
              title="Total Subsidies"
              value={summary?.total_subsidies || 0}
            />

            <KpiCard
              title="Total Allocation"
              value={formatCurrency(summary?.total_allocation || 0)}
            />

            <KpiCard
              title="Total Disbursed"
              value={formatCurrency(summary?.total_disbursed || 0)}
            />

            <KpiCard
              title="Flagged Subsidies"
              value={summary?.flagged_subsidies || 0}
            />

            <KpiCard
              title="Average Risk Score"
              value={summary?.average_risk_score || 0}
            />

          </section>

          {/* CHART GRID */}

          <section className="dashboard-grid-two">

            <div className="chart-card">
              <h2>Sector Distribution</h2>
              <SectorDistributionChart data={sectorDistribution} />
            </div>

            <div className="chart-card">
              <h2>Risk Distribution</h2>
              <RiskDistributionChart data={riskDistribution} />
            </div>

          </section>

          {/* YEAR TREND */}

          <section className="chart-card">

            <h2>Yearly Disbursement Trends</h2>

            <YearTrendChart data={yearTrends} />

          </section>

          {/* HIGH RISK TABLE */}

          <section className="chart-card">

            <h2>High Risk Subsidies</h2>

            <DataTable
              columns={highRiskColumns}
              data={highRiskSubsidies}
            />

          </section>

          {/* AUDIT SECTION */}

          <section className="dashboard-grid-two">

            <div className="chart-card">

              <h2>Recent Audit Trail</h2>

              <AuditTimeline audits={audits} />

            </div>

            <div className="chart-card">

              <h2>Audit Records</h2>

              <DataTable
                columns={auditColumns}
                data={audits}
              />

            </div>

          </section>

        </main>

      </div>

    </div>
  );
}