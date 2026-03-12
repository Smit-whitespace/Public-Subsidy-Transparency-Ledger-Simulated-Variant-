import React from "react";
import { formatCurrency } from "../../utils/formatCurrency";

export default function FundFlowOverview({ data }) {
  if (!data) {
    return <div className="chart-empty">No fund flow data available</div>;
  }

  const totalAllocated = Number(data.total_allocated || data.total_allocation || 0);
  const totalDisbursed = Number(data.total_disbursed || 0);
  const totalPending = totalAllocated - totalDisbursed;
  const completionPct = totalAllocated > 0
    ? ((totalDisbursed / totalAllocated) * 100).toFixed(1)
    : 0;

  const stages = [
    {
      label: "Allocated",
      value: totalAllocated,
      icon: "📋",
      color: "var(--color-primary)"
    },
    {
      label: "Disbursed",
      value: totalDisbursed,
      icon: "💰",
      color: "var(--color-success)"
    },
    {
      label: "Pending",
      value: totalPending > 0 ? totalPending : 0,
      icon: "⏳",
      color: "var(--color-warning)"
    }
  ];

  return (
    <div className="fund-flow-overview">
      <div className="fund-flow-pipeline">
        {stages.map((stage, i) => (
          <React.Fragment key={stage.label}>
            <div className="fund-flow-stage">
              <div className="fund-flow-stage-icon">{stage.icon}</div>
              <div className="fund-flow-stage-value">{formatCurrency(stage.value)}</div>
              <div className="fund-flow-stage-label">{stage.label}</div>
            </div>
            {i < stages.length - 1 && (
              <div className="fund-flow-arrow">→</div>
            )}
          </React.Fragment>
        ))}
      </div>
      <div className="fund-flow-progress">
        <div className="fund-flow-progress-header">
          <span>Disbursement Completion</span>
          <span className="fund-flow-progress-pct">{completionPct}%</span>
        </div>
        <div className="fund-flow-progress-bar">
          <div
            className="fund-flow-progress-fill"
            style={{ width: `${Math.min(completionPct, 100)}%` }}
          />
        </div>
      </div>
    </div>
  );
}
