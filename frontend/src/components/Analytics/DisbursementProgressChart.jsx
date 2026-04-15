import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend
} from "recharts";

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="chart-tooltip">
        <div className="chart-tooltip-label">{label}</div>
        {payload.map((entry, idx) => (
          <div key={idx} style={{ color: entry.color, fontSize: 13 }}>
            {entry.name}: ₹{entry.value?.toLocaleString('en-IN') || 0}
          </div>
        ))}
      </div>
    );
  }
  return null;
};

export default function DisbursementProgressChart({ data }) {
  if (!data || !data.length) {
    return <div className="chart-empty">No disbursement data available</div>;
  }

  const formatted = data.map(item => ({
    sector: item.sector,
    allocated: Number(item.total_allocation || 0),
    disbursed: Number(item.total_disbursed || 0)
  }));

  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart data={formatted} barGap={4}>
        <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" vertical={false} />
        <XAxis dataKey="sector" axisLine={false} tickLine={false} tick={{ fill: '#6B7280', fontSize: 11 }} />
        <YAxis
          axisLine={false}
          tickLine={false}
          tick={{ fill: '#6B7280', fontSize: 11 }}
          tickFormatter={(v) => `₹${(v / 10000000).toFixed(0)}Cr`}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(0,0,0,0.04)' }} />
        <Legend
          wrapperStyle={{ fontSize: 12, paddingTop: 8 }}
        />
        <Bar name="Allocated" dataKey="allocated" fill="#6366F1" radius={[4, 4, 0, 0]} animationDuration={1000} />
        <Bar name="Disbursed" dataKey="disbursed" fill="#22C55E" radius={[4, 4, 0, 0]} animationDuration={1200} />
      </BarChart>
    </ResponsiveContainer>
  );
}
