import React from "react";
import { CheckCircle, AlertTriangle, XCircle, Activity } from "lucide-react";

export default function SystemHealthIndicator({ anomalies = {}, flagged = 0 }) {
  const highSeverity = anomalies.high_severity_count || 0;
  const mediumSeverity = anomalies.medium_severity_count || 0;
  const totalAnomalies = anomalies.total_anomalies || 0;

  // Determine health status
  let status = "healthy";
  let statusText = "System Operating Normally";
  let statusColor = "success";

  if (highSeverity > 0 || flagged > 5) {
    status = "critical";
    statusText = "Anomalies Detected - Action Required";
    statusColor = "danger";
  } else if (mediumSeverity > 0 || flagged > 0) {
    status = "warning";
    statusText = "Warnings Detected - Monitoring";
    statusColor = "warning";
  }

  const StatusIcon = status === "critical" 
    ? XCircle 
    : status === "warning" 
      ? AlertTriangle 
      : CheckCircle;

  return (
    <div className={`system-health system-health--${statusColor}`}>
      <div className="system-health-icon">
        <StatusIcon size={20} />
      </div>
      <div className="system-health-content">
        <div className="system-health-label">System Status</div>
        <div className="system-health-value">{statusText}</div>
      </div>
      <div className="system-health-stats">
        <div className="system-health-stat">
          <span className="stat-value">{highSeverity}</span>
          <span className="stat-label">High</span>
        </div>
        <div className="system-health-stat">
          <span className="stat-value">{mediumSeverity}</span>
          <span className="stat-label">Medium</span>
        </div>
        <div className="system-health-stat">
          <span className="stat-value">{totalAnomalies}</span>
          <span className="stat-label">Total</span>
        </div>
      </div>
    </div>
  );
}