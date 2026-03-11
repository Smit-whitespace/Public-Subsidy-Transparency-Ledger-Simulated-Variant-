import React from "react";
import {
  PieChart,
  Pie,
  Tooltip,
  Legend,
  ResponsiveContainer
} from "recharts";

const COLORS = [
  "#4F46E5",
  "#22C55E",
  "#F59E0B",
  "#EF4444",
  "#06B6D4",
  "#8B5CF6"
];

export default function SectorDistributionChart({ data }) {
  if (!data || !data.length) {
    return <div>No sector data available</div>;
  }

  const formatted = data.map((item, index) => ({
    name: item.sector,
    value: Number(item.total_allocation),
    fill: COLORS[index % COLORS.length]
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={formatted}
          dataKey="value"
          nameKey="name"
          outerRadius={100}
          label={false}
        />

        <Tooltip />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}