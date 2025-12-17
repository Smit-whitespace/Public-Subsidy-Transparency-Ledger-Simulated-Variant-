import React from "react";

export default function Footer() {
  const year = new Date().getFullYear();

  return (
    <footer className="app-footer">
      <div className="footer-content">
        <div className="footer-brand">
          <div className="footer-title">Public Subsidy Transparency Ledger</div>
          <div className="footer-tagline">Clarity in public funds.</div>
        </div>
        <div className="footer-links">
          <a href="#">About</a>
          <a href="#">Documentation</a>
          <a href="#">Contact</a>
        </div>
      </div>
      <div className="footer-meta">
        © {year} Public Subsidy Transparency Ledger
      </div>
    </footer>
  );
}