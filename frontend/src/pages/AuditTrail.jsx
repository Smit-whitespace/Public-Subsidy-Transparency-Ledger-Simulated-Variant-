import React, { useState, useEffect } from "react";
import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";
import SearchBar from "../components/SearchBar";
import FilterPanel from "../components/FilterPanel";
import DataTable from "../components/DataTable";
import AuditTimeline from "../components/AuditTimeline";
import Loader from "../components/Loader";
import { fetchAudits } from "../api/audit";
import useAuth from "../hooks/useAuth";
import useFetch from "../hooks/useFetch";
import useDebounce from "../hooks/useDebounce";

export default function AuditTrail() {
  const { user, token, isAuthenticated } = useAuth();
  const [query, setQuery] = useState("");
  const [filters, setFilters] = useState({});

  const debouncedQuery = useDebounce(query, 400);

  const { data, loading, error, execute } = useFetch(
    () =>
      fetchAudits({
        limit: 50,
        offset: 0,
        entity: filters.entity || null,
        action: filters.action || null,
        token
      }),
    { immediate: true }
  );

  useEffect(() => {
    if (isAuthenticated && token) {
      execute();
    }
  }, [debouncedQuery, filters, token, isAuthenticated, execute]);

  if (!isAuthenticated) {
    return <div className="audit-trail unauthorized">Access denied</div>;
  }

  if (loading) {
    return <Loader message="Loading audit trail..." />;
  }

  if (error) {
    return <div className="audit-trail error">Failed to load audit trail</div>;
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
      key: "timestamp",
      label: "Timestamp",
      render: (row) => {
        try {
          return new Date(row.timestamp).toLocaleString();
        } catch (_) {
          return row.timestamp || "N/A";
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
      <Navbar user={user} />
      <div className="audit-layout">
        <Sidebar user={user} />
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
            <DataTable columns={columns} data={audits} />
          </section>

          <section>
            <h2>Audit Timeline</h2>
            <AuditTimeline audits={audits} />
          </section>
        </main>
      </div>
    </div>
  );
}