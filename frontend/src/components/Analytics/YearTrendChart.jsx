import React from "react";
import {
  AreaChart,
  Area,
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

export default function YearTrendChart({ data }) {
  if (!data || !data.length) {
    return <div className="chart-empty">No trend data available</div>;
  }

  const formatted = data.map((item) => ({
    year: item.year,
    disbursed: item.total_allocation || 0
  }));

  return (
    <ResponsiveContainer width="100%" height={350}>
      <AreaChart data={formatted}>
        <defs>
          <linearGradient id="colorDisbursed" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#6366F1" stopOpacity={0.3}/>
            <stop offset="95%" stopColor="#6366F1" stopOpacity={0}/>
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" vertical={false} />
        <XAxis dataKey="year" axisLine={false} tickLine={false} tick={{ fill: '#6B7280', fontSize: 12 }} />
        <YAxis 
          axisLine={false} 
          tickLine={false} 
          tick={{ fill: '#6B7280', fontSize: 12 }}
          tickFormatter={(value) => `₹${(value / 10000000).toFixed(1)}Cr`}
        />
        <Tooltip content={<CustomTooltip />} />
        <Area
          type="monotone"
          dataKey="disbursed"
          stroke="#6366F1"
          strokeWidth={3}
          fillOpacity={1}
          fill="url(#colorDisbursed)"
          animationDuration={1500}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}