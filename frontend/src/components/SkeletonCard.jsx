import React from "react";

export default function SkeletonCard({ height = 120, className = "" }) {
  return (
    <div className={`skeleton-card ${className}`} style={{ minHeight: height }}>
      <div className="skeleton-line skeleton-line-short" />
      <div className="skeleton-line skeleton-line-long" />
    </div>
  );
}

export function SkeletonKpi() {
  return (
    <div className="skeleton-card skeleton-kpi">
      <div className="skeleton-line skeleton-line-short" />
      <div className="skeleton-line skeleton-line-medium" />
    </div>
  );
}

export function SkeletonChart() {
  return (
    <div className="skeleton-card skeleton-chart">
      <div className="skeleton-line skeleton-line-short" />
      <div className="skeleton-bars">
        <div className="skeleton-bar" style={{ height: "60%" }} />
        <div className="skeleton-bar" style={{ height: "85%" }} />
        <div className="skeleton-bar" style={{ height: "45%" }} />
        <div className="skeleton-bar" style={{ height: "70%" }} />
        <div className="skeleton-bar" style={{ height: "55%" }} />
      </div>
    </div>
  );
}
