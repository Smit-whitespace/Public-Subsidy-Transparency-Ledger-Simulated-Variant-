import React from "react";

export default function DataTable({
  columns = [],
  data = [],
  loading = false,
  error = null,
  emptyMessage = "No records found"
}) {
  if (loading) {
    return <div className="data-table loading">Loading data...</div>;
  }

  if (error) {
    return <div className="data-table error">Failed to load data</div>;
  }

  if (!data || data.length === 0) {
    return <div className="data-table empty">{emptyMessage}</div>;
  }

  return (
    <div className="data-table">
      <table>
        <thead>
          <tr>
            {columns.map((col) => (
              <th key={col.key}>{col.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, index) => {
            const rowKey = row.id || index;
            return (
              <tr key={rowKey}>
                {columns.map((col) => {
                  const cellValue = col.render
                    ? col.render(row)
                    : String(row[col.key] ?? "");
                  return <td key={col.key}>{cellValue}</td>;
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}