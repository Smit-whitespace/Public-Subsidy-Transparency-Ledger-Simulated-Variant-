import React from "react";

export default function DisbursementChart({
  disbursements = [],
  loading = false,
  error = null
}) {
  if (loading) {
    return <div className="disbursement-chart loading">Loading chart...</div>;
  }

  if (error) {
    return (
      <div className="disbursement-chart error">
        Failed to load disbursement chart
      </div>
    );
  }

  if (!disbursements || disbursements.length === 0) {
    return (
      <div className="disbursement-chart empty">
        No disbursement data available
      </div>
    );
  }

  function parseAmount(value) {
    if (typeof value === "number") return value;
    const parsed = parseFloat(value);
    return isNaN(parsed) ? 0 : parsed;
  }

  function formatDate(dateValue) {
    try {
      return new Date(dateValue).toLocaleDateString();
    } catch (_) {
      return String(dateValue || "N/A");
    }
  }

  const sortedData = [...disbursements].sort((a, b) => {
    try {
      return new Date(a.date) - new Date(b.date);
    } catch (_) {
      return 0;
    }
  });

  const amounts = sortedData.map((item) => parseAmount(item.amount));
  const maxAmount = Math.max(...amounts, 1);

  return (
    <div className="disbursement-chart">
      {sortedData.map((item, index) => {
        const itemKey = item.id || index;
        const amount = parseAmount(item.amount);
        const percentage = Math.min(100, Math.max(0, (amount / maxAmount) * 100));
        const formattedDate = formatDate(item.date);

        return (
          <div className="chart-row" key={itemKey}>
            <div className="chart-label">{formattedDate}</div>
            <div className="chart-bar-wrapper">
              <div
                className="chart-bar"
                style={{ width: `${percentage}%` }}
                title={`Amount: ${amount}`}
              ></div>
            </div>
            <div className="chart-value">{amount}</div>
          </div>
        );
      })}
    </div>
  );
}