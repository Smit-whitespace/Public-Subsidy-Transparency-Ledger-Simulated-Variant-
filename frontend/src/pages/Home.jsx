import React from "react";
import { Link, Navigate } from "react-router-dom";
import { DollarSign, Shield, Link2, Eye, ArrowRight } from "lucide-react";

import Navbar from "../components/Navbar";
import Footer from "../components/Footer";
import { useAuth } from "../context/AuthContext";

const HOW_IT_WORKS = [
  {
    icon: DollarSign,
    colorClass: "how-icon--1",
    title: "Money Flows Tracked",
    desc: "Every rupee is tracked from allocation through projects to final disbursement, creating a complete financial trail."
  },
  {
    icon: Shield,
    colorClass: "how-icon--2",
    title: "Anomalies Detected",
    desc: "AI-powered risk scoring and anomaly detection identifies suspicious patterns, duplicate payments, and irregularities."
  },
  {
    icon: Link2,
    colorClass: "how-icon--3",
    title: "Blockchain Proof",
    desc: "Critical records are anchored on-chain, providing immutable proof that records have not been tampered with."
  },
  {
    icon: Eye,
    colorClass: "how-icon--4",
    title: "Full Transparency",
    desc: "Public portal provides open access to subsidy data, risk scores, and transparency rankings without login."
  }
];

export default function Home() {
  const { isAuthenticated } = useAuth();

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="home-page">
      <Navbar />
      <main className="home-content">
        <section className="home-hero">
          <h1>Public Subsidy Transparency Ledger</h1>
          <p>Clarity in public funds. Transparency by design.</p>
          <div className="home-hero-actions">
            <Link to="/transparency" className="cta-primary">Explore Transparency Portal</Link>
            <Link to="/login" className="cta-link" style={{ marginLeft: "16px" }}>Login</Link>
          </div>
        </section>

        <section className="home-how-it-works">
          <h2 style={{ textAlign: "center", fontSize: 26, fontWeight: 700, letterSpacing: "-0.5px" }}>How It Works</h2>
          <p style={{ textAlign: "center", color: "var(--color-text-secondary)", marginBottom: 8, fontSize: 15 }}>From allocation to accountability — every step is monitored.</p>
          <div className="how-it-works-grid">
            {HOW_IT_WORKS.map((item, idx) => (
              <div key={idx} className="how-it-works-card">
                <div className={`how-icon ${item.colorClass}`}>
                  <item.icon size={28} color="white" />
                </div>
                <div className="how-title">{item.title}</div>
                <div className="how-desc">{item.desc}</div>
              </div>
            ))}
          </div>
        </section>

        <section style={{ padding: "40px 24px 60px", maxWidth: 900, margin: "0 auto", textAlign: "center" }}>
          <h2 style={{ fontSize: 22, fontWeight: 700, marginBottom: 24 }}>Subsidy Lifecycle</h2>
          <div className="lifecycle-flow">
            <div className="lifecycle-step">
              <div className="lifecycle-step-icon" style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)" }}>
                <DollarSign size={22} color="white" />
              </div>
              <div className="lifecycle-step-label">Allocation</div>
            </div>
            <ArrowRight size={20} className="lifecycle-arrow" />
            <div className="lifecycle-step">
              <div className="lifecycle-step-icon" style={{ background: "linear-gradient(135deg, #06b6d4, #0ea5e9)" }}>
                <Link2 size={22} color="white" />
              </div>
              <div className="lifecycle-step-label">Project Assignment</div>
            </div>
            <ArrowRight size={20} className="lifecycle-arrow" />
            <div className="lifecycle-step">
              <div className="lifecycle-step-icon" style={{ background: "linear-gradient(135deg, #22c55e, #14b8a6)" }}>
                <DollarSign size={22} color="white" />
              </div>
              <div className="lifecycle-step-label">Disbursement</div>
            </div>
            <ArrowRight size={20} className="lifecycle-arrow" />
            <div className="lifecycle-step">
              <div className="lifecycle-step-icon" style={{ background: "linear-gradient(135deg, #f59e0b, #f97316)" }}>
                <Shield size={22} color="white" />
              </div>
              <div className="lifecycle-step-label">Audit and Verification</div>
            </div>
          </div>
        </section>

        <section className="home-features">
          <h2>What this platform provides</h2>
          <ul>
            <li>End-to-end tracking of subsidy allocation</li>
            <li>Immutable audit trails for accountability</li>
            <li>Disbursement timelines and visual insights</li>
            <li>On-chain proof of records</li>
            <li>AI-powered anomaly detection</li>
            <li>Public transparency portal</li>
          </ul>
        </section>

        <section className="home-cta">
          <p>Explore how public funds move from allocation to measurable impact.</p>
          <Link to="/transparency" className="cta-link">View Transparency Portal</Link>
        </section>
      </main>
      <Footer />
    </div>
  );
}
