import React from "react";

export default function SubsidyCard({ subsidy = null, onClick = () => {} }) {
  if (!subsidy) {
    return <div className="subsidy-card empty">No subsidy data</div>;
  }

  function handleClick() {
    onClick(subsidy);
  }

  function handleKeyDown(e) {
    if (e.key === "Enter") {
      onClick(subsidy);
    }
  }

  const name = subsidy.name || "Untitled Subsidy";
  const description = subsidy.description || "No description available";
  const status = subsidy.status || "Unknown";
  const amount = subsidy.amount ? String(subsidy.amount) : "N/A";
  const allocatedAmount = subsidy.allocated_amount
    ? String(subsidy.allocated_amount)
    : "N/A";
  const disbursedAmount = subsidy.disbursed_amount
    ? String(subsidy.disbursed_amount)
    : "N/A";

  return (
    <div
      className="subsidy-card"
      role="button"
      tabIndex={0}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
    >
      <div className="subsidy-card-header">
        <div className="subsidy-title">{name}</div>
        <div className="subsidy-status">{status}</div>
      </div>
      <div className="subsidy-card-body">
        <div className="subsidy-description">{description}</div>
      </div>
      <div className="subsidy-card-meta">
        <div className="subsidy-amount">Total: {amount}</div>
        <div className="subsidy-progress">
          Allocated: {allocatedAmount} • Disbursed: {disbursedAmount}
        </div>
      </div>
    </div>
  );
}