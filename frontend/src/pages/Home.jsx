import React from "react";
import { Link, Navigate } from "react-router-dom";

import Navbar from "../components/Navbar";
import Footer from "../components/Footer";

import { useAuth } from "../context/AuthContext";

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

          <p>
            Clarity in public funds. Transparency by design.
          </p>

          <div className="home-hero-actions">

            <Link
              to="/login"
              className="cta-primary"
            >
              Login to Continue
            </Link>

          </div>

        </section>

        <section className="home-features">

          <h2>What this platform provides</h2>

          <ul>
            <li>End-to-end tracking of subsidy allocation</li>
            <li>Immutable audit trails for accountability</li>
            <li>Disbursement timelines and visual insights</li>
            <li>On-chain proof of records</li>
          </ul>

        </section>

        <section className="home-cta">

          <p>
            Explore how public funds move from allocation to measurable impact.
          </p>

          <Link
            to="/login"
            className="cta-link"
          >
            Go to Dashboard
          </Link>

        </section>

      </main>

      <Footer />

    </div>
  );
}