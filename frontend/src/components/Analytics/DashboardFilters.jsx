import React from "react";

export default function DashboardFilters({
  sectors,
  filters,
  onChange,
  onReset
}) {
  function handleChange(key, value) {
    onChange({ ...filters, [key]: value });
  }

  const hasActiveFilters = filters.sector || filters.riskLevel || filters.yearFrom || filters.yearTo || filters.search;

  return (
    <div className="dashboard-filters">
      <div className="dashboard-filters-row">
        <div className="filter-group">
          <label className="filter-label" htmlFor="df-sector">Sector</label>
          <select
            id="df-sector"
            className="filter-control"
            value={filters.sector || ""}
            onChange={(e) => handleChange("sector", e.target.value)}
          >
            <option value="">All Sectors</option>
            {(sectors || []).map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label className="filter-label" htmlFor="df-risk">Risk Level</label>
          <select
            id="df-risk"
            className="filter-control"
            value={filters.riskLevel || ""}
            onChange={(e) => handleChange("riskLevel", e.target.value)}
          >
            <option value="">All Levels</option>
            <option value="high">High Risk</option>
            <option value="medium">Medium Risk</option>
            <option value="low">Low Risk</option>
          </select>
        </div>

        <div className="filter-group">
          <label className="filter-label" htmlFor="df-year-from">Year From</label>
          <input
            id="df-year-from"
            className="filter-control"
            type="number"
            min="2000"
            max="2099"
            placeholder="e.g. 2020"
            value={filters.yearFrom || ""}
            onChange={(e) => handleChange("yearFrom", e.target.value)}
          />
        </div>

        <div className="filter-group">
          <label className="filter-label" htmlFor="df-year-to">Year To</label>
          <input
            id="df-year-to"
            className="filter-control"
            type="number"
            min="2000"
            max="2099"
            placeholder="e.g. 2024"
            value={filters.yearTo || ""}
            onChange={(e) => handleChange("yearTo", e.target.value)}
          />
        </div>

        <div className="filter-group filter-group-search">
          <label className="filter-label" htmlFor="df-search">Search</label>
          <input
            id="df-search"
            className="filter-control"
            type="text"
            placeholder="Search subsidies..."
            value={filters.search || ""}
            onChange={(e) => handleChange("search", e.target.value)}
          />
        </div>

        {hasActiveFilters && (
          <div className="filter-actions">
            <button type="button" onClick={onReset}>Reset</button>
          </div>
        )}
      </div>
    </div>
  );
}
