import React from "react";

const SEVERITY_CONFIG = {
  high: { label: "High", className: "anomaly-severity--high" },
  medium: { label: "Medium", className: "anomaly-severity--medium" },
  low: { label: "Low", className: "anomaly-severity--low" }
};

export default function AnomalySummaryPanel({ data }) {
  if (!data) {
    return <div className="chart-empty">No anomaly data available</div>;
  }

  const alerts = data.alerts || data.anomalies || [];
  const totalAlerts = data.total_alerts || alerts.length || 0;
  const highSeverity = data.high_severity || alerts.filter(a => a.severity === "high").length || 0;
  const mediumSeverity = data.medium_severity || alerts.filter(a => a.severity === "medium").length || 0;

  return (
    <div className="anomaly-panel">
      <div className="anomaly-summary-strip">
        <div className="anomaly-stat">
          <span className="anomaly-stat-value">{totalAlerts}</span>
          <span className="anomaly-stat-label">Total Alerts</span>
        </div>
        <div className="anomaly-stat anomaly-stat--danger">
          <span className="anomaly-stat-value">{highSeverity}</span>
          <span className="anomaly-stat-label">High Severity</span>
        </div>
        <div className="anomaly-stat anomaly-stat--warning">
          <span className="anomaly-stat-value">{mediumSeverity}</span>
          <span className="anomaly-stat-label">Medium Severity</span>
        </div>
      </div>

      {alerts.length > 0 && (
        <div className="anomaly-list">
          {alerts.slice(0, 8).map((alert, index) => {
            const severity = alert.severity || "medium";
            const config = SEVERITY_CONFIG[severity] || SEVERITY_CONFIG.medium;
            return (
              <div key={alert.id || index} className="anomaly-item">
                <span className={`anomaly-severity ${config.className}`}>
                  {config.label}
                </span>
                <span className="anomaly-type">{alert.type || alert.event_type || "Anomaly"}</span>
                <span className="anomaly-description">
                  {alert.description || alert.message || "Suspicious activity detected"}
                </span>
              </div>
            );
          })}
        </div>
      )}

      {alerts.length === 0 && totalAlerts === 0 && (
        <div className="anomaly-clean">
          <span className="anomaly-clean-icon">✓</span>
          <span>No anomalies detected — system is healthy</span>
        </div>
      )}
    </div>
  );
}
