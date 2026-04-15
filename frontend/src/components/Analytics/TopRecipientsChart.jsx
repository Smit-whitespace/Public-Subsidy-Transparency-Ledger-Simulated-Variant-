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

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="chart-tooltip">
        <div className="chart-tooltip-label">{label}</div>
        <div className="chart-tooltip-value">₹{payload[0].value?.toLocaleString('en-IN') || 0}</div>
      </div>
    );
  }
  return null;
};

export default function TopRecipientsChart({ data }) {
  if (!data || !data.length) {
    return <div className="chart-empty">No recipient data available</div>;
  }

  const formatted = data.slice(0, 8).map(item => ({
    name: item.recipient?.length > 20 ? item.recipient.substring(0, 20) + '…' : item.recipient,
    amount: Number(item.total_allocation || item.amount || 0)
  }));

  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart data={formatted} layout="vertical" barSize={16}>
        <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" horizontal={false} />
        <XAxis
          type="number"
          axisLine={false}
          tickLine={false}
          tick={{ fill: '#6B7280', fontSize: 11 }}
          tickFormatter={(v) => `₹${(v / 10000000).toFixed(1)}Cr`}
        />
        <YAxis
          type="category"
          dataKey="name"
          width={130}
          axisLine={false}
          tickLine={false}
          tick={{ fill: '#6B7280', fontSize: 11 }}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(0,0,0,0.04)' }} />
        <Bar dataKey="amount" fill="#6366F1" radius={[0, 6, 6, 0]} animationDuration={1000} />
      </BarChart>
    </ResponsiveContainer>
  );
}
