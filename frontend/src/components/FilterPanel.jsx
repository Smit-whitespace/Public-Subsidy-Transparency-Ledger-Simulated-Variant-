import React from "react";

export default function FilterPanel({
  filters = {},
  schema = [],
  onChange = () => {},
  onReset = () => {}
}) {
  function handleChange(key, value) {
    const updatedFilters = { ...filters, [key]: value };
    onChange(updatedFilters);
  }

  return (
    <div className="filter-panel">
      {schema.map((field) => {
        const { key, label, type, options } = field;
        const value = filters[key] || "";

        return (
          <div className="filter-group" key={key}>
            <label className="filter-label" htmlFor={key}>
              {label}
            </label>
            {type === "text" && (
              <input
                className="filter-control"
                type="text"
                id={key}
                value={value}
                onChange={(e) => handleChange(key, e.target.value)}
              />
            )}
            {type === "date" && (
              <input
                className="filter-control"
                type="date"
                id={key}
                value={value}
                onChange={(e) => handleChange(key, e.target.value)}
              />
            )}
            {type === "select" && (
              <select
                className="filter-control"
                id={key}
                value={value}
                onChange={(e) => handleChange(key, e.target.value)}
              >
                <option value="">All</option>
                {options &&
                  options.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
              </select>
            )}
          </div>
        );
      })}
      <div className="filter-actions">
        <button type="button" onClick={onReset}>
          Reset
        </button>
      </div>
    </div>
  );
}