import React, { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";

import Navbar from "../components/Navbar";
import Footer from "../components/Footer";
import Loader from "../components/Loader";

import { getPublicSubsidyById } from "../services/publicService";
import { formatCurrency } from "../utils/formatCurrency";
import { formatDate } from "../utils/formatDate";
import { getRiskLevel } from "../utils/riskLevel";

export default function PublicSubsidyDetail() {
  const { id } = useParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const result = await getPublicSubsidyById(id);
        setData(result);
      } catch (err) {
        setError("Failed to load subsidy details.");
      } finally {
        setLoading(false);
      }
    }
    if (id) load();
  }, [id]);

  if (loading) return <Loader message="Loading subsidy details..." />;

  if (error || !data) {
    return (
      <div className="public-transparency">
        <Navbar />
        <main className="public-content">
          <div className="error">{error || "Subsidy not found"}</div>
          <Link to="/transparency" className="cta-link" style={{ marginTop: "1rem", display: "inline-block" }}>
            ← Back to Transparency Portal
          </Link>
        </main>
        <Footer />
      </div>
    );
  }

  const { subsidy, projects, disbursement_summary } = data;

  return (
    <div className="public-transparency">
      <Navbar />

      <main className="public-content">
        <Link to="/transparency" className="back-link">← Back to Transparency Portal</Link>

        <section className="public-detail-header">
          <h1>{subsidy.title}</h1>
          <div className="public-detail-meta">
            <span className={`subsidy-status ${subsidy.status}`}>{subsidy.status}</span>
            <span className={`risk-badge ${getRiskLevel(subsidy.risk_score)}`}>
              {getRiskLevel(subsidy.risk_score)} risk
            </span>
          </div>
        </section>

        <section className="public-detail-grid">
          <div className="detail-card">
            <h3>Allocation Details</h3>
            <dl className="detail-list">
              <dt>Recipient</dt>
              <dd>{subsidy.recipient}</dd>
              <dt>Sector</dt>
              <dd>{subsidy.sector}</dd>
              <dt>Total Allocation</dt>
              <dd>{formatCurrency(subsidy.total_allocation)}</dd>
              <dt>Period</dt>
              <dd>{formatDate(subsidy.start_date)} — {formatDate(subsidy.end_date)}</dd>
            </dl>
          </div>

          <div className="detail-card">
            <h3>Transparency Metrics</h3>
            <div className="metric-row">
              <span className="metric-label">Transparency Score</span>
              <div className="transparency-bar">
                <div
                  className="transparency-fill"
                  style={{ width: `${Math.min(100, parseFloat(subsidy.transparency_score))}%` }}
                />
                <span className="transparency-text">
                  {parseFloat(subsidy.transparency_score).toFixed(0)}%
                </span>
              </div>
            </div>
            <div className="metric-row">
              <span className="metric-label">Risk Score</span>
              <div className="transparency-bar">
                <div
                  className="transparency-fill"
                  style={{
                    width: `${Math.min(100, parseFloat(subsidy.risk_score))}%`,
                    background: parseFloat(subsidy.risk_score) >= 70
                      ? "var(--color-danger)"
                      : parseFloat(subsidy.risk_score) >= 40
                        ? "var(--color-warning)"
                        : "var(--color-success)",
                  }}
                />
                <span className="transparency-text">
                  {parseFloat(subsidy.risk_score).toFixed(0)}/100
                </span>
              </div>
            </div>
          </div>

          <div className="detail-card">
            <h3>Disbursement Progress</h3>
            <dl className="detail-list">
              <dt>Total Disbursed</dt>
              <dd>{formatCurrency(disbursement_summary.total_disbursed)}</dd>
              <dt>Remaining</dt>
              <dd>{formatCurrency(disbursement_summary.remaining)}</dd>
              <dt>Completion</dt>
              <dd>{disbursement_summary.completion_percent}%</dd>
              <dt>Payments Made</dt>
              <dd>{disbursement_summary.count}</dd>
            </dl>
            <div className="progress-bar-container">
              <div
                className="progress-bar-fill"
                style={{ width: `${Math.min(100, disbursement_summary.completion_percent)}%` }}
              />
            </div>
          </div>
        </section>

        {subsidy.description && (
          <section className="detail-card" style={{ marginBottom: "28px" }}>
            <h3>Description</h3>
            <p style={{ color: "var(--color-text-secondary)", fontSize: "14px", lineHeight: "1.6" }}>
              {subsidy.description}
            </p>
          </section>
        )}

        {projects.length > 0 && (
          <section className="public-projects-section">
            <h2>Linked Projects ({projects.length})</h2>
            <div className="public-projects-list">
              {projects.map((p) => (
                <div key={p.id} className="public-project-item">
                  <div className="public-project-name">{p.name}</div>
                  <div className="public-project-meta">
                    <span className={`project-status ${p.status}`}>{p.status}</span>
                    {p.owner && <span>Owner: {p.owner}</span>}
                    {p.start_date && <span>Started: {formatDate(p.start_date)}</span>}
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        <section className="public-cta">
          <p>Want full access to audit trails, anomaly detection, and detailed reports?</p>
          <Link to="/login" className="cta-primary">Login for Full Access</Link>
        </section>
      </main>

      <Footer />
    </div>
  );
}
