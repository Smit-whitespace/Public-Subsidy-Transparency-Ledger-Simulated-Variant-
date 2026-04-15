import React from "react";

export default function RiskBadge({ score }) {

  let level = "low";

  if (score > 70) level = "high";
  else if (score > 40) level = "medium";

  return (
    <span className={`risk-badge ${level}`}>
      {score}
    </span>
  );
}