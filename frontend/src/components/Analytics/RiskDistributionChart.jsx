import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Cell
} from "recharts";

const RISK_COLORS = {
  low: "#22C55E",
  medium: "#F59E0B",
  high: "#EF4444"
};

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="chart-tooltip">
        <div className="chart-tooltip-label">{label}</div>
        <div className="chart-tooltip-value">{payload[0].value} subsidies</div>
      </div>
    );
  }
  return null;
};

export default function RiskDistributionChart({ data }) {
  if (!data) {
    return <div className="chart-empty">No risk data available</div>;
  }

  const formatted = Object.entries(data).map(([key, value]) => ({
    risk: key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
    count: value,
    key: key.toLowerCase()
  }));

  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart data={formatted} barSize={50}>
        <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" vertical={false} />
        <XAxis dataKey="risk" axisLine={false} tickLine={false} tick={{ fill: '#6B7280', fontSize: 12 }} />
        <YAxis axisLine={false} tickLine={false} tick={{ fill: '#6B7280', fontSize: 12 }} />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(0,0,0,0.04)' }} />
        <Bar dataKey="count" radius={[6, 6, 0, 0]} animationDuration={1000}>
          {formatted.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={RISK_COLORS[entry.key] || '#6366F1'} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}