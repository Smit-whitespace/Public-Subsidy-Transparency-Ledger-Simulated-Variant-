import React, { useState, useEffect, useMemo } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AlertTriangle, Filter, Search as SearchIcon, TrendingUp, Shield } from "lucide-react";

import Navbar from "../components/Navbar";
import Footer from "../components/Footer";
import Loader from "../components/Loader";
import KpiCard from "../components/Analytics/KpiCard";
import SectorDistributionChart from "../components/Analytics/SectorDistributionChart";
import YearTrendChart from "../components/Analytics/YearTrendChart";
import RiskDistributionChart from "../components/Analytics/RiskDistributionChart";
import SearchBar from "../components/SearchBar";

import {
  getPublicSummary,
  getPublicSectorDistribution,
  getPublicYearTrends,
  getPublicRiskDistribution,
  getPublicSubsidies,
  getPublicTransparencyScores,
  getPublicFundFlow,
} from "../services/publicService";

import { formatCurrency } from "../utils/formatCurrency";
import { getRiskLevel } from "../utils/riskLevel";

export default function PublicTransparency() {
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [summary, setSummary] = useState(null);
  const [sectorData, setSectorData] = useState([]);
  const [yearData, setYearData] = useState([]);
  const [riskData, setRiskData] = useState(null);
  const [subsidies, setSubsidies] = useState([]);
  const [allSubsidies, setAllSubsidies] = useState([]);
  const [transparencyScores, setTransparencyScores] = useState([]);
  const [fundFlow, setFundFlow] = useState(null);

  const [searchQuery, setSearchQuery] = useState("");
  const [sectorFilter, setSectorFilter] = useState("");
  const [riskFilter, setRiskFilter] = useState("");
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      setError(null);
      try {
        const [summaryRes, sectorRes, yearRes, riskRes, subsidyRes, scoreRes, flowRes] =
          await Promise.all([
            getPublicSummary(),
            getPublicSectorDistribution(),
            getPublicYearTrends(),
            getPublicRiskDistribution(),
            getPublicSubsidies({ limit: 50 }),
            getPublicTransparencyScores({ limit: 10 }),
            getPublicFundFlow(),
          ]);

        setSummary(summaryRes);
        setSectorData(sectorRes);
        setYearData(yearRes);
        setRiskData(riskRes);
        setAllSubsidies(subsidyRes?.items || []);
        setSubsidies(subsidyRes?.items || []);
        setTransparencyScores(scoreRes || []);
        setFundFlow(flowRes);
      } catch (err) {
        setError("Failed to load transparency data. Please try again later.");
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const sectors = useMemo(() => {
    const s = new Set();
    allSubsidies.forEach(item => { if (item.sector) s.add(item.sector); });
    return Array.from(s).sort();
  }, [allSubsidies]);

  const filteredSubsidies = useMemo(() => {
    let result = allSubsidies;

    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      result = result.filter(s =>
        s.title?.toLowerCase().includes(q) ||
        s.recipient?.toLowerCase().includes(q)
      );
    }
    if (sectorFilter) {
      result = result.filter(s => s.sector === sectorFilter);
    }
    if (riskFilter) {
      result = result.filter(s => getRiskLevel(s.risk_score) === riskFilter);
    }

    return result;
  }, [allSubsidies, searchQuery, sectorFilter, riskFilter]);

  const highRiskCount = useMemo(() => {
    return allSubsidies.filter(s => getRiskLevel(s.risk_score) === 'high').length;
  }, [allSubsidies]);

  function handleSearch() {
    setSubsidies(filteredSubsidies);
  }

  function handleResetFilters() {
    setSearchQuery("");
    setSectorFilter("");
    setRiskFilter("");
    setSubsidies(allSubsidies);
  }

  function getTransparencyColor(score) {
    const num = parseFloat(score);
    if (num >= 70) return "var(--color-success)";
    if (num >= 40) return "var(--color-warning)";
    return "var(--color-danger)";
  }

  if (loading) {
    return <Loader message="Loading public transparency data..." />;
  }

  if (error) {
    return (
      <div className="public-transparency">
        <Navbar />
        <main className="public-content">
          <div className="error">{error}</div>
        </main>
        <Footer />
      </div>
    );
  }

  return (
    <div className="public-transparency">
      <Navbar />

      <main className="public-content">
        {/* ANOMALY ALERTS BANNER */}
        {highRiskCount > 0 && (
          <div className="anomaly-alert-banner">
            <AlertTriangle size={18} />
            <span>
              <strong>{highRiskCount} high-risk {highRiskCount === 1 ? 'subsidy' : 'subsidies'}</strong> detected.
              These programs require enhanced oversight.
            </span>
          </div>
        )}

        {/* HERO */}
        <section className="public-hero">
          <h1>Public Subsidy Transparency Portal</h1>
          <p>Open access to government subsidy allocation data, disbursement tracking, and transparency scores.</p>
        </section>

        {/* KPI STRIP */}
        <section className="public-kpis">
          <KpiCard title="Total Subsidies" value={summary?.total_subsidies || 0} icon="subsidies" color="primary" tooltip="Total subsidy programs tracked" />
          <KpiCard title="Active Programs" value={summary?.active_subsidies || 0} icon="active" color="success" tooltip="Currently active subsidy programs" />
          <KpiCard title="Total Allocation" value={formatCurrency(summary?.total_allocation || 0)} icon="allocation" color="info" />
          <KpiCard title="Total Disbursed" value={formatCurrency(summary?.total_disbursed || 0)} icon="disbursed" color="success" />
          <KpiCard title="Completion Rate" value={`${summary?.completion_rate_percent || 0}%`} icon="completion" color="primary" />
        </section>

        {/* FUND FLOW SUMMARY */}
        {fundFlow && (
          <section className="public-fund-flow">
            <h2>Fund Flow Overview</h2>
            <div className="fund-flow-cards">
              <div className="fund-flow-card">
                <div className="fund-flow-label">Subsidies → Projects</div>
                <div className="fund-flow-value">{fundFlow.total_projects || 0} projects</div>
                <div className="fund-flow-meta">{fundFlow.total_subsidies || 0} subsidies</div>
              </div>
              <div className="fund-flow-card">
                <div className="fund-flow-label">Projects → Disbursements</div>
                <div className="fund-flow-value">{fundFlow.total_disbursements || 0} payments</div>
                <div className="fund-flow-meta">{formatCurrency(fundFlow.total_disbursed || 0)} disbursed</div>
              </div>
              <div className="fund-flow-card">
                <div className="fund-flow-label">Disbursement Rate</div>
                <div className="fund-flow-value">{fundFlow.disbursement_rate_percent || 0}%</div>
                <div className="fund-flow-meta">{formatCurrency(fundFlow.remaining_to_disburse || 0)} remaining</div>
              </div>
            </div>
          </section>
        )}

        {/* CHARTS */}
        <section className="public-charts">
          <div className="dashboard-grid-two">
            <div className="chart-card">
              <h2>Allocation by Sector</h2>
              <SectorDistributionChart data={sectorData} />
            </div>
            <div className="chart-card">
              <h2>Risk Distribution</h2>
              <RiskDistributionChart data={riskData} />
            </div>
          </div>

          <div className="chart-card">
            <h2>Yearly Funding Trends</h2>
            <YearTrendChart data={yearData} />
          </div>
        </section>

        {/* TRANSPARENCY LEADERBOARD */}
        <section className="public-transparency-scores">
          <h2>
            <Shield size={18} style={{ verticalAlign: "middle", marginRight: 8 }} />
            Transparency Leaderboard
          </h2>
          <div className="transparency-list">
            {transparencyScores.map((item) => (
              <div key={item.id} className="transparency-item" onClick={() => navigate(`/public/subsidies/${item.id}`)}>
                <div className="transparency-item-info">
                  <div className="transparency-item-title">{item.title}</div>
                  <div className="transparency-item-meta">{item.sector} · {item.recipient}</div>
                </div>
                <div className="transparency-item-scores">
                  <div className="transparency-item-score">
                    <span className="score-label">Transparency</span>
                    <span className="score-value" style={{ color: getTransparencyColor(item.transparency_score) }}>
                      {parseFloat(item.transparency_score).toFixed(0)}%
                    </span>
                  </div>
                  <div className="transparency-item-score">
                    <span className="score-label">Risk</span>
                    <span className={`risk-badge ${getRiskLevel(item.risk_score)}`}>
                      {getRiskLevel(item.risk_score)}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* SEARCH & EXPLORE SUBSIDIES */}
        <section className="public-search-section">
          <div className="public-search-header">
            <h2>
              <SearchIcon size={18} style={{ verticalAlign: "middle", marginRight: 8 }} />
              Explore Subsidies
            </h2>
            <button
              className="btn-secondary"
              onClick={() => setShowFilters(!showFilters)}
              style={{ padding: "6px 14px", fontSize: 12 }}
            >
              <Filter size={14} style={{ verticalAlign: "middle", marginRight: 4 }} />
              {showFilters ? 'Hide Filters' : 'Advanced Filters'}
            </button>
          </div>

          <div className="public-search-controls">
            <SearchBar
              value={searchQuery}
              onChange={setSearchQuery}
              onSubmit={handleSearch}
              placeholder="Search by title or recipient..."
            />
          </div>

          {showFilters && (
            <div className="public-advanced-filters">
              <div className="filter-group">
                <label className="filter-label">Sector</label>
                <select className="filter-control" value={sectorFilter} onChange={(e) => setSectorFilter(e.target.value)}>
                  <option value="">All Sectors</option>
                  {sectors.map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
              <div className="filter-group">
                <label className="filter-label">Risk Level</label>
                <select className="filter-control" value={riskFilter} onChange={(e) => setRiskFilter(e.target.value)}>
                  <option value="">All Levels</option>
                  <option value="high">High Risk</option>
                  <option value="medium">Medium Risk</option>
                  <option value="low">Low Risk</option>
                </select>
              </div>
              <div className="filter-actions">
                <button onClick={handleSearch}>Apply</button>
                <button onClick={handleResetFilters} style={{ marginLeft: 8 }}>Reset</button>
              </div>
            </div>
          )}

          <div className="public-subsidies-grid">
            {filteredSubsidies.length > 0 ? (
              filteredSubsidies.slice(0, 20).map((s) => (
                <div
                  key={s.id}
                  className="public-subsidy-card"
                  onClick={() => navigate(`/public/subsidies/${s.id}`)}
                >
                  <div className="public-subsidy-header">
                    <div className="public-subsidy-title">{s.title}</div>
                    <span className={`risk-badge ${getRiskLevel(s.risk_score)}`}>
                      {getRiskLevel(s.risk_score)} risk
                    </span>
                  </div>
                  <div className="public-subsidy-meta">
                    <span>{s.sector}</span>
                    <span>{s.recipient}</span>
                  </div>
                  <div className="public-subsidy-footer">
                    <span className="public-subsidy-amount">{formatCurrency(s.total_allocation)}</span>
                    <span className={`subsidy-status ${s.status}`}>{s.status}</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="empty">No subsidies found matching your criteria</div>
            )}
          </div>

          {filteredSubsidies.length > 20 && (
            <div style={{ textAlign: 'center', marginTop: 16, color: 'var(--color-text-muted)', fontSize: 13 }}>
              Showing 20 of {filteredSubsidies.length} results
            </div>
          )}
        </section>

        {/* CTA */}
        <section className="public-cta">
          <p>Want full access to analytics, audit trails, and detailed reports?</p>
          <Link to="/login" className="cta-primary">Login for Full Access</Link>
        </section>
      </main>

      <Footer />
    </div>
  );
}
