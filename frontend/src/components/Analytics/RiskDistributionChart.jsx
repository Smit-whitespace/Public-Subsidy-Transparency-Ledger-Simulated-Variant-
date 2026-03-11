import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid
} from "recharts";

export default function RiskDistributionChart({ data }) {
  // Backend returns object {low_risk, medium_risk, high_risk}, not array
  if (!data) {
    return <div>No risk data available</div>;
  }

  // Convert object to array format for Recharts
  const formatted = Object.entries(data).map(([key, value]) => ({
    risk: key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
    count: value
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={formatted}>
        <CartesianGrid strokeDasharray="3 3" />

        <XAxis dataKey="risk" />
        <YAxis />

        <Tooltip />

        <Bar dataKey="count" fill="#EF4444" />
      </BarChart>
    </ResponsiveContainer>
  );
}