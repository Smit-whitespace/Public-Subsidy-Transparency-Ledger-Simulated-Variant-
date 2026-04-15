import React, { useState, useEffect, useCallback } from "react";
import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";
import SearchBar from "../components/SearchBar";
import FilterPanel from "../components/FilterPanel";
import DataTable from "../components/DataTable";
import AuditTimeline from "../components/AuditTimeline";
import Loader from "../components/Loader";

import { fetchAudits } from "../services/auditService";
import { useAuth } from "../context/AuthContext";
import useFetch from "../hooks/useFetch";
import useDebounce from "../hooks/useDebounce";

export default function AuditTrail() {

  const { token, isAuthenticated } = useAuth();

  const [query, setQuery] = useState("");
  const [filters, setFilters] = useState({});
  const [debouncedFilters, setDebouncedFilters] = useState({});

  // Debounce filter changes to avoid instant API calls
  const debouncedEntity = useDebounce(filters.entity, 500);
  const debouncedAction = useDebounce(filters.action, 500);

  // Update debounced filters only when debounced values change
  useEffect(() => {
    setDebouncedFilters({
      entity: debouncedEntity,
      action: debouncedAction
    });
  }, [debouncedEntity, debouncedAction]);

  const fetchAuditData = useCallback(() => {

    if (!token) {
      return Promise.resolve([]);
    }

    return fetchAudits({
      limit: 50,
      offset: 0,
      entity: debouncedFilters.entity || null,
      action: debouncedFilters.action || null,
      token
    });

  }, [debouncedFilters, token]);

  const {
    data,
    loading,
    error,
    execute
  } = useFetch(fetchAuditData, { immediate: true });

useEffect(() => {
  if (isAuthenticated && token) {
    execute();
  }
}, [debouncedFilters, token, isAuthenticated, execute]);

  if (!isAuthenticated) {
    return (
      <div className="audit-trail unauthorized">
        Access denied
      </div>
    );
  }

  if (loading) {
    return <Loader message="Loading audit trail..." />;
  }

  if (error) {
    return (
      <div className="audit-trail error">
        Failed to load audit trail
      </div>
    );
  }

  const audits = data?.data || data || [];

  const filterSchema = [
    {
      key: "entity",
      label: "Entity",
      type: "text"
    },
    {
      key: "action",
      label: "Action",
      type: "text"
    }
  ];

  const columns = [
    {
      key: "action",
      label: "Action",
      render: (row) => row.action || "N/A"
    },
    {
      key: "entity",
      label: "Entity",
      render: (row) => row.entity || "N/A"
    },
    {
      key: "entity_id",
      label: "Entity ID",
      render: (row) => row.entity_id || "N/A"
    },
    {
      key: "actor",
      label: "Actor",
      render: (row) => row.performed_by || "system"
    },
    {
      key: "created_at",
      label: "Timestamp",
      render: (row) => {
        // Backend field is created_at, not timestamp
        const ts = row.created_at || row.timestamp;
        try {
          return new Date(ts).toLocaleString();
        } catch (_) {
          return ts || "N/A";
        }
      }
    }
  ];

  function handleFilterChange(updatedFilters) {
    setFilters(updatedFilters);
  }

  function handleFilterReset() {
    setFilters({});
  }

  return (
    <div className="audit-trail">

      <Navbar />

      <div className="audit-layout">

        <Sidebar />

        <main className="audit-content">

          <h1>Audit Trail</h1>
          <p>Chronological record of system actions</p>

          <section>
            <SearchBar
              value={query}
              onChange={setQuery}
              onSubmit={() => {}}
              placeholder="Search audits..."
            />
          </section>

          <section>
            <FilterPanel
              filters={filters}
              schema={filterSchema}
              onChange={handleFilterChange}
              onReset={handleFilterReset}
            />
          </section>

          <section>
            <h2>Audit Records</h2>
            <DataTable
              columns={columns}
              data={audits}
            />
          </section>

          <section>
            <h2>Audit Timeline</h2>
            <AuditTimeline
              audits={audits}
            />
          </section>

        </main>

      </div>

    </div>
  );
}