import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid
} from "recharts";

export default function YearTrendChart({ data }) {
  if (!data || !data.length) {
    return <div>No trend data available</div>;
  }

  // Backend sends total_allocation, not total_disbursed
  const formatted = data.map((item) => ({
    year: item.year,
    disbursed: item.total_allocation || 0
  }));

  return (
    <ResponsiveContainer width="100%" height={350}>
      <LineChart data={formatted}>
        <CartesianGrid strokeDasharray="3 3" />

        <XAxis dataKey="year" />
        <YAxis />

        <Tooltip />

        <Line
          type="monotone"
          dataKey="disbursed"
          stroke="#4F46E5"
          strokeWidth={3}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}