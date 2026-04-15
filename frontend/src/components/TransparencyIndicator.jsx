import React from "react";

export default function TransparencyIndicator({ value }) {

  const width = Math.min(Math.max(value, 0), 100);

  return (
    <div className="transparency-bar">

      <div
        className="transparency-fill"
        style={{ width: `${width}%` }}
      />

      <span className="transparency-text">
        {value}%
      </span>

    </div>
  );
}