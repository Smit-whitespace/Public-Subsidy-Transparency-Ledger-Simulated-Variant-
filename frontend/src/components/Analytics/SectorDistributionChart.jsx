import React from "react";
import {
  PieChart,
  Pie,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell
} from "recharts";

const MODERN_COLORS = [
  "#6366F1", "#22C55E", "#F59E0B", "#EF4444", "#06B6D4",
  "#8B5CF6", "#EC4899", "#14B8A6", "#F97316", "#64748B"
];

const CustomTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="chart-tooltip">
        <div className="chart-tooltip-label">{data.name}</div>
        <div className="chart-tooltip-value">₹{data.value?.toLocaleString('en-IN') || 0}</div>
        {data.percent && <div className="chart-tooltip-percent">{data.percent}%</div>}
      </div>
    );
  }
  return null;
};

const CustomLegend = ({ payload }) => (
  <div className="chart-custom-legend">
    {payload.map((entry, index) => (
      <div key={index} className="legend-item">
        <span className="legend-color" style={{ backgroundColor: entry.color }} />
        <span className="legend-label">{entry.value}</span>
      </div>
    ))}
  </div>
);

export default function SectorDistributionChart({ data, showLegend = true }) {
  if (!data || !data.length) {
    return <div className="chart-empty">No sector data available</div>;
  }

  const total = data.reduce((sum, item) => sum + (Number(item.total_allocation) || 0), 0);

  const formatted = data.map((item, index) => ({
    name: item.sector,
    value: Number(item.total_allocation),
    percent: total > 0 ? ((Number(item.total_allocation) / total) * 100).toFixed(1) : 0,
    fill: MODERN_COLORS[index % MODERN_COLORS.length]
  }));

  return (
    <ResponsiveContainer width="100%" height={320}>
      <PieChart>
        <Pie
          data={formatted}
          dataKey="value"
          nameKey="name"
          cx="50%"
          cy="50%"
          outerRadius={110}
          innerRadius={50}
          paddingAngle={2}
          animationBegin={0}
          animationDuration={1000}
          animationEasing="ease-out"
        >
          {formatted.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.fill} stroke="transparent" />
          ))}
        </Pie>
        <Tooltip content={<CustomTooltip />} />
        {showLegend && <Legend content={<CustomLegend />} />}
      </PieChart>
    </ResponsiveContainer>
  );
}