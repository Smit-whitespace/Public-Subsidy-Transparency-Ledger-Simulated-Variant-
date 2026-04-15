import React, { useCallback, useState, useMemo } from "react";
import { Link } from "react-router-dom";
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
import SystemHealthIndicator from "../components/Analytics/SystemHealthIndicator";
import DisbursementProgressChart from "../components/Analytics/DisbursementProgressChart";
import TopRecipientsChart from "../components/Analytics/TopRecipientsChart";
import DemoInsightsPanel from "../components/Analytics/DemoInsightsPanel";
import { useAuth } from "../context/AuthContext";
import { useDemoMode } from "../context/DemoModeContext";
import { Eye, EyeOff, Plus, Wallet, FolderKanban, ArrowRightLeft, AlertCircle } from "lucide-react";
import useFetch from "../hooks/useFetch";
import {
  getDashboardSummary,
  getSectorDistribution,
  getRiskDistribution,
  getYearTrends,
  getHighRiskSubsidies,
  getAnomalySummary,
  getFundFlowSummary,
  getFundFlowBySector,
  getSectorRiskOverview,
  getFraudNetwork
} from "../services/analyticsService";
import { getAudits } from "../services/auditService";
import { formatCurrency } from "../utils/formatCurrency";

export default function AdminDashboard() {
  const { user, token, isAuthenticated } = useAuth();
  const { demoMode, toggleDemo } = useDemoMode();
  const [filters, setFilters] = useState({ sector: "", riskLevel: "", search: "" });
  const [dateRange, setDateRange] = useState({ start: "", end: "" });

  const fetchAudits = useCallback(() => {
    if (!token) return Promise.resolve([]);
    return getAudits(token, 15, 0);
  }, [token]);

  const fetchSummary = useCallback(() => getDashboardSummary(), []);
  const fetchSector = useCallback(() => getSectorDistribution(), []);
  const fetchRisk = useCallback(() => getRiskDistribution(), []);
  const fetchYear = useCallback(() => getYearTrends(), []);

  const fetchHighRisk = useCallback(() => {
    return getHighRiskSubsidies(10, filters.sector || null);
  }, [filters.sector]);

  const fetchAnomalies = useCallback(() => getAnomalySummary(), []);
  const fetchFundFlow = useCallback(() => getFundFlowSummary(), []);
  const fetchFundFlowSector = useCallback(() => getFundFlowBySector(), []);
  const fetchSectorRisk = useCallback(() => getSectorRiskOverview(), []);
  const fetchFraudNetwork = useCallback(() => getFraudNetwork(), []);

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

  const {
    data: anomalies,
    loading: anomaliesLoading
  } = useFetch(fetchAnomalies, { immediate: true });

  const {
    data: fundFlow,
    loading: fundFlowLoading
  } = useFetch(fetchFundFlow, { immediate: true });

  const {
    data: fundFlowSector,
    loading: fundFlowSectorLoading
  } = useFetch(fetchFundFlowSector, { immediate: true });

  const {
    data: sectorRisk,
    loading: sectorRiskLoading
  } = useFetch(fetchSectorRisk, { immediate: true });

  const {
    data: fraudNetwork,
    loading: fraudNetworkLoading
  } = useFetch(fetchFraudNetwork, { immediate: true });

  const sectors = useMemo(() => {
    const s = new Set();
    if (sectorDistribution) {
      sectorDistribution.forEach(item => { if (item.sector) s.add(item.sector); });
    }
    return Array.from(s).sort();
  }, [sectorDistribution]);

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const handleResetFilters = () => {
    setFilters({ sector: "", riskLevel: "", search: "" });
    setDateRange({ start: "", end: "" });
  };

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
    highRiskLoading ||
    anomaliesLoading ||
    fundFlowLoading ||
    fundFlowSectorLoading ||
    sectorRiskLoading ||
    fraudNetworkLoading;

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
  const anomalyData = anomalies || {};
  const fundFlowData = fundFlow || {};
  const fundFlowSectorData = fundFlowSector || [];
  const sectorRiskData = sectorRisk || [];
  const fraudData = fraudNetwork || {};

  const completionRate = summary?.total_allocation > 0 
    ? Math.round((summary?.total_disbursed / summary?.total_allocation) * 100) 
    : 0;

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
      label: "Subsidy",
      render: (row) => <Link to={`/subsidies/${row.id}`} className="table-link">{row.title}</Link>
    },
    {
      key: "recipient",
      label: "Recipient"
    },
    {
      key: "sector",
      label: "Sector"
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
        <TransparencyIndicator value={row.transparency_score || 0} />
      )
    }
  ];

  const sectorRiskColumns = [
    { key: "sector", label: "Sector", render: (row) => <span className="sector-risk-name">{row.sector}</span> },
    { key: "subsidy_count", label: "Subsidies" },
    { key: "total_allocation", label: "Total", render: (row) => formatCurrency(row.total_allocation || 0) },
    { key: "avg_risk_score", label: "Avg Risk", render: (row) => <RiskBadge score={Math.round(row.avg_risk_score || 0)} /> },
    { key: "flagged_count", label: "Flagged", render: (row) => row.flagged_count > 0 ? <span className="sector-flagged">{row.flagged_count}</span> : <span className="sector-clean">0</span> }
  ];

  /* ---------- RENDER ---------- */

  return (
    <div className="admin-dashboard">

      <Navbar />

      <div className="admin-layout">

        <Sidebar />

        <main className="admin-content">

          <header className="dashboard-header">
            <div className="dashboard-header-top">
              <div>
                <h1>PSTL Intelligence Dashboard</h1>
                <p>System-wide transparency and subsidy intelligence</p>
              </div>
              <div className="dashboard-header-meta">
                {/* Admin Create Buttons */}
                <div className="admin-create-buttons">
                  <Link to="/admin/create-subsidy" className="admin-create-btn" title="Create Subsidy">
                    <Plus size={14} /><Wallet size={14} />
                  </Link>
                  <Link to="/admin/create-project" className="admin-create-btn" title="Create Project">
                    <Plus size={14} /><FolderKanban size={14} />
                  </Link>
                  <Link to="/admin/create-disbursement" className="admin-create-btn" title="Create Disbursement">
                    <Plus size={14} /><ArrowRightLeft size={14} />
                  </Link>
                </div>
                <button
                  className={`demo-toggle ${demoMode ? 'active' : ''}`}
                  onClick={toggleDemo}
                >
                  <div className="demo-toggle-switch" />
                  <span className="demo-toggle-label">
                    {demoMode ? <Eye size={14} /> : <EyeOff size={14} />}
                    {' '}Demo Insights
                  </span>
                </button>
                <span className="dashboard-user-badge">{user?.role || 'User'}</span>
              </div>
            </div>
          </header>

          {/* INTERACTIVE FILTERS */}
          <section className="dashboard-filters">
            <div className="dashboard-filters-row">
              <div className="filter-group-search">
                <label className="filter-label">Search</label>
                <input
                  type="search"
                  className="filter-control"
                  placeholder="Search subsidies..."
                  value={filters.search}
                  onChange={(e) => handleFilterChange('search', e.target.value)}
                />
              </div>
              <div className="filter-group">
                <label className="filter-label">Sector</label>
                <select
                  className="filter-control"
                  value={filters.sector}
                  onChange={(e) => handleFilterChange('sector', e.target.value)}
                >
                  <option value="">All Sectors</option>
                  {sectors.map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
              <div className="filter-group">
                <label className="filter-label">Risk Level</label>
                <select
                  className="filter-control"
                  value={filters.riskLevel}
                  onChange={(e) => handleFilterChange('riskLevel', e.target.value)}
                >
                  <option value="">All Levels</option>
                  <option value="high">High Risk</option>
                  <option value="medium">Medium Risk</option>
                  <option value="low">Low Risk</option>
                </select>
              </div>
              <div className="filter-group">
                <label className="filter-label">Start Date</label>
                <input
                  type="date"
                  className="filter-control"
                  value={dateRange.start}
                  onChange={(e) => setDateRange(prev => ({ ...prev, start: e.target.value }))}
                />
              </div>
              <div className="filter-group">
                <label className="filter-label">End Date</label>
                <input
                  type="date"
                  className="filter-control"
                  value={dateRange.end}
                  onChange={(e) => setDateRange(prev => ({ ...prev, end: e.target.value }))}
                />
              </div>
              <div className="filter-actions">
                <button type="button" onClick={handleResetFilters}>Reset</button>
              </div>
            </div>
          </section>

          {/* DEMO MODE BANNER */}
          {demoMode && (
            <div className="demo-mode-banner">
              <AlertCircle size={18} />
              <span>Demo Mode – Data generated for demonstration purposes. This is not real government data.</span>
            </div>
          )}

          {/* SYSTEM HEALTH INDICATOR */}
          <div className="dashboard-health">
            <SystemHealthIndicator anomalies={anomalyData} flagged={summary?.flagged_subsidies || 0} />
          </div>

          {/* KPI STRIP */}

          <section className="dashboard-kpis">

            <KpiCard
              title="Total Subsidies"
              value={summary?.total_subsidies || 0}
              icon="subsidies"
              color="primary"
              tooltip="Total number of subsidy programs in the system"
              trend={5}
              trendLabel="vs last month"
            />

            <KpiCard
              title="Total Allocation"
              value={summary?.total_allocation || 0}
              icon="allocation"
              color="info"
              tooltip="Total amount allocated across all subsidies"
              prefix="₹"
            />

            <KpiCard
              title="Total Disbursed"
              value={summary?.total_disbursed || 0}
              icon="disbursed"
              color="success"
              tooltip="Total amount disbursed to recipients"
              prefix="₹"
            />

            <KpiCard
              title="Flagged Subsidies"
              value={summary?.flagged_subsidies || 0}
              icon="flagged"
              color="danger"
              tooltip="Subsidies flagged for potential anomalies or risks"
            />

            <KpiCard
              title="Average Risk Score"
              value={summary?.average_risk_score || 0}
              icon="risk"
              color="warning"
              tooltip="System-wide average risk score (0-100)"
              suffix="/100"
              decimals={1}
            />

          </section>

          {/* DEMO INSIGHTS */}
          <DemoInsightsPanel />

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

          {/* FUND FLOW OVERVIEW */}

          <section className="chart-card">
            <div className="chart-card-header">
              <h2>Fund Flow Pipeline</h2>
            </div>
            <div className="fund-flow-overview">
              <div className="fund-flow-pipeline">
                <div className="fund-flow-stage">
                  <div className="fund-flow-stage-icon">💰</div>
                  <div className="fund-flow-stage-value">{formatCurrency(fundFlowData.total_allocated || 0)}</div>
                  <div className="fund-flow-stage-label">Allocated</div>
                </div>
                <span className="fund-flow-arrow">→</span>
                <div className="fund-flow-stage">
                  <div className="fund-flow-stage-icon">📋</div>
                  <div className="fund-flow-stage-value">{fundFlowData.project_count || 0}</div>
                  <div className="fund-flow-stage-label">Projects</div>
                </div>
                <span className="fund-flow-arrow">→</span>
                <div className="fund-flow-stage">
                  <div className="fund-flow-stage-icon">💸</div>
                  <div className="fund-flow-stage-value">{formatCurrency(fundFlowData.total_disbursed || 0)}</div>
                  <div className="fund-flow-stage-label">Disbursed</div>
                </div>
              </div>
              <div className="fund-flow-progress">
                <div className="fund-flow-progress-header">
                  <span>Disbursement Rate</span>
                  <span className="fund-flow-progress-pct">{fundFlowData.disbursement_rate || completionRate}%</span>
                </div>
                <div className="fund-flow-progress-bar">
                  <div className="fund-flow-progress-fill" style={{width: `${fundFlowData.disbursement_rate || completionRate}%`}} />
                </div>
              </div>
            </div>
          </section>

          {/* ANOMALY DETECTION PANEL */}

          <section className="chart-card">
            <div className="chart-card-header">
              <h2>Anomaly Detection</h2>
              <span className="chart-card-badge">AI-Powered</span>
            </div>
            <div className="anomaly-panel">
              <div className="anomaly-summary-strip">
                <div className="anomaly-stat anomaly-stat--danger">
                  <span className="anomaly-stat-value">{anomalyData.high_severity_count || 0}</span>
                  <span className="anomaly-stat-label">High Risk</span>
                </div>
                <div className="anomaly-stat anomaly-stat--warning">
                  <span className="anomaly-stat-value">{anomalyData.medium_severity_count || 0}</span>
                  <span className="anomaly-stat-label">Medium Risk</span>
                </div>
                <div className="anomaly-stat">
                  <span className="anomaly-stat-value">{anomalyData.total_anomalies || 0}</span>
                  <span className="anomaly-stat-label">Total Anomalies</span>
                </div>
              </div>
              {anomalyData.recent_anomalies?.length > 0 ? (
                <div className="anomaly-list">
                  {anomalyData.recent_anomalies.slice(0, 5).map((anomaly, idx) => (
                    <div className="anomaly-item" key={idx}>
                      <span className={`anomaly-severity anomaly-severity--${anomaly.severity || 'low'}`}>{anomaly.severity || 'low'}</span>
                      <span className="anomaly-type">{anomaly.type || 'Unknown'}</span>
                      <span className="anomaly-description">{anomaly.description}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="anomaly-clean">
                  <span className="anomaly-clean-icon">✓</span>
                  No anomalies detected - System operating normally
                </div>
              )}
            </div>
          </section>

          {/* YEAR TREND */}

          <section className="chart-card">
            <h2>Yearly Disbursement Trends</h2>
            <YearTrendChart data={yearTrends} />
          </section>

          {/* DISBURSEMENT PROGRESS BY SECTOR */}

          <section className="chart-card">
            <div className="chart-card-header">
              <h2>Disbursement Progress by Sector</h2>
            </div>
            <DisbursementProgressChart data={fundFlowSectorData} />
          </section>

          {/* TOP RECIPIENTS */}

          <section className="chart-card">
            <div className="chart-card-header">
              <h2>Top Recipients by Allocation</h2>
            </div>
            <TopRecipientsChart data={highRiskSubsidies} />
          </section>

          {/* HIGH RISK TABLE */}

          <section className="chart-card">
            <div className="chart-card-header">
              <h2>High Risk Subsidies</h2>
            </div>
            <DataTable
              columns={highRiskColumns}
              data={highRiskSubsidies}
              emptyMessage="No high-risk subsidies found"
            />
          </section>

          {/* SECTOR RISK TABLE */}

          <section className="chart-card">
            <div className="chart-card-header">
              <h2>Sector Risk Overview</h2>
            </div>
            <div className="sector-risk-table">
              <DataTable
                columns={sectorRiskColumns}
                data={sectorRiskData}
                emptyMessage="No sector data available"
              />
            </div>
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