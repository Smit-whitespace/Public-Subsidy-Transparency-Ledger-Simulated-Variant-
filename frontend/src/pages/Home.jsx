import React from "react";
import Navbar from "../components/Navbar";
import Footer from "../components/Footer";

export default function Home() {
  return (
    <div className="home-page">
      <Navbar />
      <main className="home-content">
        <section className="home-hero">
          <h1>Public Subsidy Transparency Ledger</h1>
          <p>Clarity in public funds. Transparency by design.</p>
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
          <p>Explore how public funds move from allocation to impact.</p>
          <a href="#" className="cta-link">
            Go to Dashboard
          </a>
        </section>
      </main>
      <Footer />
    </div>
  );
}