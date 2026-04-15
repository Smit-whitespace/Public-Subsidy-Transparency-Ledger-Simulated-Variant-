import React from "react";
import { formatCurrency } from "../../utils/formatCurrency";
import { getRiskLevel } from "../../utils/riskLevel";

export default function SectorRiskTable({ data, onSectorClick }) {
  if (!data || !data.length) {
    return <div className="chart-empty">No sector risk data available</div>;
  }

  const sorted = [...data].sort((a, b) => b.avg_risk_score - a.avg_risk_score);

  return (
    <div className="sector-risk-table">
      <table>
        <thead>
          <tr>
            <th>Sector</th>
            <th>Subsidies</th>
            <th>Allocation</th>
            <th>Avg Risk</th>
            <th>Flagged</th>
            <th>Risk Level</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((row) => {
            const level = getRiskLevel(row.avg_risk_score);
            return (
              <tr
                key={row.sector}
                className="sector-risk-row"
                onClick={() => onSectorClick && onSectorClick(row.sector)}
              >
                <td className="sector-risk-name">{row.sector}</td>
                <td>{row.subsidy_count}</td>
                <td>{formatCurrency(row.total_allocation)}</td>
                <td>
                  <span className="sector-risk-score">{row.avg_risk_score}</span>
                </td>
                <td>
                  {row.flagged_count > 0 ? (
                    <span className="sector-flagged">{row.flagged_count}</span>
                  ) : (
                    <span className="sector-clean">0</span>
                  )}
                </td>
                <td>
                  <span className={`risk-badge ${level}`}>
                    {level}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
