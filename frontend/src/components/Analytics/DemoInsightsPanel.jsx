import React from "react";
import { useDemoMode } from "../../context/DemoModeContext";
import { AlertTriangle, Zap, Eye } from "lucide-react";

export default function DemoInsightsPanel() {
  const { demoMode, demoInsights } = useDemoMode();

  if (!demoMode) return null;

  return (
    <section className="demo-insights-panel">
      <div className="demo-insights-header">
        <Eye size={18} />
        <h2>Demo Insights Active</h2>
        <span className="chart-card-badge">Presentation Mode</span>
      </div>

      <div className="demo-highlights">
        {demoInsights.highlights.map((h, idx) => (
          <div key={idx} className="demo-highlight-item">
            <Zap size={14} />
            <span>{h}</span>
          </div>
        ))}
      </div>

      <div className="demo-fraud-cases">
        <h3>Example Fraud Cases</h3>
        {demoInsights.fraudCases.map(fc => (
          <div key={fc.id} className={`suspicious-item severity-${fc.severity}`}>
            <div className="suspicious-header">
              <span className={`severity-badge ${fc.severity}`}>{fc.severity}</span>
              <span className="suspicious-type">{fc.title}</span>
            </div>
            <div className="suspicious-desc">{fc.description}</div>
            <div className="demo-case-meta">
              <span>Sector: {fc.sector}</span>
              <span>Recipient: {fc.recipient}</span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
